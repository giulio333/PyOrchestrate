"""Agent lifecycle management for registration, startup, and termination."""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from PyOrchestrate.core.agent.base_agent import BaseAgent, AgentProtocol
from PyOrchestrate.core.base.base import BaseClass
from PyOrchestrate.core.orchestrator.memory import (
    OMemory,
    AgentEntry,
    AgentLifecycleState,
    AgentStartAttempt,
)
from PyOrchestrate.core.utilities.messaging import MessageChannel


class LifecycleStartStatus(Enum):
    """Outcome of one authoritative lifecycle startup attempt."""

    STARTED = "started"
    CANCELLED = "cancelled"
    FAILED_CLEAN = "failed_clean"
    FAILED_LIVE = "failed_live"


@dataclass(frozen=True)
class LifecycleStartResult:
    """Typed result returned by :meth:`AgentLifecycleManager.start_agent`."""

    status: LifecycleStartStatus
    reason: str | None = None

    @property
    def started(self) -> bool:
        return self.status is LifecycleStartStatus.STARTED

    @property
    def live_failure(self) -> bool:
        return self.status is LifecycleStartStatus.FAILED_LIVE


class AgentLifecycleManager:
    """Authoritative owner of agent lifecycle state transitions."""

    _FAILED_START_CLEANUP_TIMEOUT = 2.0
    _START_WAIT_POLL_INTERVAL = 0.05

    def __init__(
        self,
        memory: OMemory,
        config: BaseClass.Config,
        logger,
        before_start: Callable[[str, int], None] | None = None,
    ):
        self.memory = memory
        self.config = config
        self.logger = logger
        self.before_start = before_start
        # Registration mutates shared memory. Blocking lifecycle operations
        # intentionally do not hold this manager-wide lock.
        self._lock = threading.RLock()

    def register_agent(
        self,
        agent_class: type[AgentProtocol],
        name: str,
        custom_config: BaseClass.Config | None = None,
        custom_plugin: BaseClass.Plugin | None = None,
        control_events: BaseAgent.ControlEvents | None = None,
        state_events: BaseAgent.StateEvents | None = None,
        msg_channel: MessageChannel | None = None,
        **kwargs,
    ) -> AgentEntry:
        """Register an agent without creating its concrete instance."""
        with self._lock:
            agent_entry = self.memory.add_agent(
                agent_class=agent_class,
                name=name,
                custom_config=custom_config,
                custom_plugin=custom_plugin,
                control_events=control_events,
                state_events=state_events,
                msg_channel=msg_channel,
                **kwargs,
            )
        self.logger.debug(f"Agent '{name}' registered.")
        return agent_entry

    def prepare_start(self, agent_name: str) -> AgentStartAttempt:
        """Prepare a non-blocking startup attempt for scheduler ownership."""
        return self.get_agent(agent_name)._prepare_start()

    def execute_start(
        self,
        agent_name: str,
        attempt: AgentStartAttempt,
    ) -> LifecycleStartResult:
        """Create and start one prepared generation with bounded acknowledgement."""
        agent = self.get_agent(agent_name)
        if agent._attempt_cancel_requested(attempt):
            return self._finish_failed_start(agent, attempt, cancelled=True)
        try:
            if not agent._initialize_instance(attempt):
                return self._finish_failed_start(agent, attempt, cancelled=True)
            if agent._attempt_cancel_requested(attempt):
                return self._finish_failed_start(agent, attempt, cancelled=True)
            if self.before_start:
                self.before_start(agent_name, attempt.generation_id)
            if agent._attempt_cancel_requested(attempt):
                return self._finish_failed_start(agent, attempt, cancelled=True)
            if not agent._start_instance(attempt):
                return self._finish_failed_start(agent, attempt, cancelled=True)
        except Exception as error:
            self.logger.error(f"Failed to start agent '{agent_name}': {error}")
            return self._finish_failed_start(agent, attempt, reason=str(error))

        start_event = agent.state_events.start_event if agent.state_events else None
        deadline = time.monotonic() + self.config.agent_start_timeout
        while start_event and not start_event.is_set():
            if agent._attempt_cancel_requested(attempt):
                return self._finish_failed_start(agent, attempt, cancelled=True)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                reason = (
                    f"startup acknowledgement timed out after "
                    f"{self.config.agent_start_timeout}s"
                )
                self.logger.error(f"Agent '{agent_name}' {reason}.")
                return self._finish_failed_start(agent, attempt, reason=reason)
            start_event.wait(min(self._START_WAIT_POLL_INTERVAL, remaining))

        if agent._attempt_cancel_requested(attempt):
            return self._finish_failed_start(agent, attempt, cancelled=True)

        try:
            agent._transition_attempt_to(
                attempt,
                AgentLifecycleState.RUNNING,
                {AgentLifecycleState.STARTING},
            )
        except RuntimeError:
            if agent._attempt_cancel_requested(attempt):
                return self._finish_failed_start(agent, attempt, cancelled=True)
            raise

        self.logger.info(f"Agent '{agent_name}' started successfully.")
        return LifecycleStartResult(LifecycleStartStatus.STARTED)

    def start_agent(self, agent_name: str) -> LifecycleStartResult:
        """Prepare and execute a fresh generation without scheduler accounting."""
        attempt = self.prepare_start(agent_name)
        return self.execute_start(agent_name, attempt)

    def restart_agent(self, agent_name: str) -> LifecycleStartResult:
        """Restart through the same guarded startup path as a first start."""
        return self.start_agent(agent_name)

    def _finish_failed_start(
        self,
        agent: AgentEntry,
        attempt: AgentStartAttempt,
        *,
        cancelled: bool = False,
        reason: str | None = None,
    ) -> LifecycleStartResult:
        try:
            cleaned = self._cleanup_failed_start(agent, attempt)
        except Exception as cleanup_error:
            # Unknown cleanup errors must be treated conservatively: releasing
            # ownership could make a live instance invisible to the scheduler.
            self.logger.exception(
                f"Unexpected cleanup failure for agent '{agent.name}': "
                f"{cleanup_error}"
            )
            try:
                cleaned = not agent.is_alive(attempt)
            except Exception:
                cleaned = False
        current = agent.state
        allowed = {
            AgentLifecycleState.STARTING,
            AgentLifecycleState.STOPPING,
            AgentLifecycleState.QUARANTINED,
        }

        if not cleaned:
            if current is not AgentLifecycleState.QUARANTINED:
                agent._transition_attempt_to(
                    attempt,
                    AgentLifecycleState.QUARANTINED,
                    allowed,
                )
            return LifecycleStartResult(
                LifecycleStartStatus.FAILED_LIVE,
                reason or "agent remained alive after startup cleanup",
            )

        target = (
            AgentLifecycleState.TERMINATED if cancelled else AgentLifecycleState.FAILED
        )
        if current in allowed:
            agent._transition_attempt_to(attempt, target, allowed)
        return LifecycleStartResult(
            (
                LifecycleStartStatus.CANCELLED
                if cancelled
                else LifecycleStartStatus.FAILED_CLEAN
            ),
            reason,
        )

    def _cleanup_failed_start(
        self,
        agent: AgentEntry,
        attempt: AgentStartAttempt,
    ) -> bool:
        """Attempt bounded cleanup and report whether no live instance remains."""
        if not agent._has_instance(attempt):
            return True

        try:
            agent._stop_instance(attempt)
        except Exception as stop_error:
            self.logger.error(
                f"Failed to stop agent '{agent.name}' after startup failure: "
                f"{stop_error}"
            )

        try:
            agent._join_instance(
                timeout=self._FAILED_START_CLEANUP_TIMEOUT,
                attempt=attempt,
            )
        except Exception as join_error:
            self.logger.error(
                f"Failed to join agent '{agent.name}' after startup failure: "
                f"{join_error}"
            )

        if not agent.is_alive(attempt):
            return True

        instance = agent.instance
        terminate = getattr(instance, "terminate", None)
        if callable(terminate) and instance.a_type == "process":
            self.logger.warning(
                f"Force-terminating failed process agent '{agent.name}'."
            )
            try:
                terminate()
                agent._join_instance(
                    timeout=self._FAILED_START_CLEANUP_TIMEOUT,
                    attempt=attempt,
                )
            except Exception as terminate_error:
                self.logger.error(
                    f"Failed to force-terminate process agent '{agent.name}': "
                    f"{terminate_error}"
                )

        if agent.is_alive(attempt):
            self.logger.critical(
                f"Agent '{agent.name}' is still alive and has been quarantined."
            )
            return False
        return True

    def stop_agent(self, agent_name: str) -> None:
        """Cancel startup or request stop without waiting on another agent."""
        agent = self.get_agent(agent_name)
        state, attempt = agent._request_stop()

        if state in {
            AgentLifecycleState.REGISTERED,
            AgentLifecycleState.TERMINATED,
            AgentLifecycleState.FAILED,
            AgentLifecycleState.STOPPING,
        }:
            return

        if attempt is None or not agent.is_alive(attempt):
            # A concurrent startup owns the final STARTING/STOPPING outcome.
            if state is not AgentLifecycleState.STARTING:
                agent._transition_to(
                    AgentLifecycleState.TERMINATED,
                    {AgentLifecycleState.STOPPING},
                )
            return

        try:
            agent._stop_instance(attempt)
        except Exception:
            if agent.is_alive(attempt):
                agent._transition_to(
                    AgentLifecycleState.QUARANTINED,
                    {AgentLifecycleState.STOPPING},
                )
            else:
                agent._transition_to(
                    AgentLifecycleState.FAILED,
                    {AgentLifecycleState.STOPPING},
                )
            raise
        self.logger.info(f"Stop requested for agent '{agent_name}'.")

    def stop_all(self) -> None:
        """Request stop for every registered agent."""
        errors: list[Exception] = []
        for agent in self.memory.agents:
            try:
                self.stop_agent(agent.name)
            except Exception as error:
                errors.append(error)
                self.logger.error(f"Failed to stop agent '{agent.name}': {error}")
        if errors:
            raise ExceptionGroup("Failed to stop one or more agents", errors)

    def shutdown_all(self, timeout: float | None = None) -> list[str]:
        """Stop every agent, wait for termination, and escalate on survivors.

        Unlike :meth:`stop_all`, which only requests cooperative termination,
        this is the blocking path used when the orchestrator itself is going
        down: agents must be gone before channels and plugins are torn down.

        Args:
            timeout: Overall budget in seconds for the cooperative wait. The
                budget is shared by all agents. ``None`` waits indefinitely.

        Returns:
            list[str]: Names of the agents that are still alive afterwards.
        """
        try:
            self.stop_all()
        except ExceptionGroup:
            # stop_all() already logged every individual failure. Shutdown must
            # continue: an agent whose stop request failed is still joined and
            # escalated below.
            pass

        deadline = None if timeout is None else time.monotonic() + timeout

        for agent in self.memory.agents:
            if not agent.is_initialized or not agent.is_alive():
                continue
            remaining = (
                None if deadline is None else max(0.0, deadline - time.monotonic())
            )
            try:
                agent._join_instance(timeout=remaining)
            except Exception as error:
                self.logger.error(f"Failed to join agent '{agent.name}': {error}")

        survivors: list[str] = []
        for agent in self.memory.agents:
            if agent.is_initialized and agent.is_alive():
                if not self._escalate_shutdown(agent):
                    survivors.append(agent.name)
                    continue
            self.mark_terminated(agent.name)

        return survivors

    def _escalate_shutdown(self, agent: AgentEntry) -> bool:
        """Force-terminate a surviving agent and report whether it is gone."""
        instance = agent.instance
        terminate = getattr(instance, "terminate", None)
        if callable(terminate) and instance.a_type == "process":
            self.logger.warning(
                f"Force-terminating process agent '{agent.name}' during shutdown."
            )
            try:
                terminate()
                agent._join_instance(timeout=self._FAILED_START_CLEANUP_TIMEOUT)
            except Exception as error:
                self.logger.error(
                    f"Failed to force-terminate process agent '{agent.name}': {error}"
                )

        if not agent.is_alive():
            return True

        self.logger.critical(
            f"Agent '{agent.name}' did not terminate during shutdown "
            "and has been quarantined."
        )
        try:
            agent._transition_to(
                AgentLifecycleState.QUARANTINED,
                {
                    AgentLifecycleState.STARTING,
                    AgentLifecycleState.RUNNING,
                    AgentLifecycleState.STOPPING,
                    AgentLifecycleState.QUARANTINED,
                },
            )
        except RuntimeError as error:
            self.logger.error(
                f"Could not quarantine surviving agent '{agent.name}': {error}"
            )
        return False

    def join_agent(self, agent_name: str, timeout: float | None = None) -> None:
        """Join an initialized concrete instance through lifecycle ownership."""
        self.get_agent(agent_name)._join_instance(timeout=timeout)

    def is_attempt_alive(
        self,
        agent_name: str,
        attempt: AgentStartAttempt,
    ) -> bool:
        """Return whether the instance owned by ``attempt`` remains alive."""
        return self.get_agent(agent_name).is_alive(attempt)

    def mark_terminated(self, agent_name: str) -> None:
        """Record termination observed by the orchestrator."""
        agent = self.get_agent(agent_name)
        state = agent.state
        if state is AgentLifecycleState.TERMINATED:
            return
        if state is AgentLifecycleState.FAILED and not agent.is_alive():
            return
        agent._transition_to(
            AgentLifecycleState.TERMINATED,
            {
                AgentLifecycleState.STARTING,
                AgentLifecycleState.RUNNING,
                AgentLifecycleState.STOPPING,
                AgentLifecycleState.QUARANTINED,
            },
        )

    def get_agent(self, agent_name: str) -> AgentEntry:
        agent = self.memory.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found.")
        return agent

    def get_all_agents(self) -> list[AgentEntry]:
        return self.memory.agents
