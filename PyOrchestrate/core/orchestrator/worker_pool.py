"""Worker-pool capacity reservation and agent scheduling."""

import threading
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from PyOrchestrate.core.orchestrator.lifecycle_manager import (
    LifecycleStartResult,
    LifecycleStartStatus,
)
from PyOrchestrate.core.orchestrator.memory import AgentStartAttempt

if TYPE_CHECKING:
    from PyOrchestrate.core.orchestrator.lifecycle_manager import AgentLifecycleManager


class WorkerStartStatus(Enum):
    """Scheduler-level outcome of a start request."""

    STARTED = "started"
    QUEUED = "queued"
    CANCELLED = "cancelled"
    FAILED_CLEAN = "failed_clean"
    FAILED_LIVE = "failed_live"


@dataclass(frozen=True)
class WorkerStartResult:
    """Typed scheduler result that preserves lifecycle failure semantics."""

    status: WorkerStartStatus
    reason: str | None = None

    @property
    def started(self) -> bool:
        return self.status is WorkerStartStatus.STARTED

    @property
    def queued(self) -> bool:
        return self.status is WorkerStartStatus.QUEUED


class WorkerPoolScheduler:
    """Reserve capacity and schedule agents without blocking the pool lock."""

    def __init__(
        self, max_workers: int, lifecycle_manager: "AgentLifecycleManager", logger
    ):
        self.max_workers = max_workers
        self.lifecycle_manager = lifecycle_manager
        self.logger = logger

        self._starting_agents: set[str] = set()
        self._started_agents: set[str] = set()
        self._failed_live_agents: set[str] = set()
        self._waiting_queue: deque[str] = deque()
        self._accepting_starts = True
        self._lock = threading.RLock()

    def _occupied_count_unlocked(self) -> int:
        return (
            len(self._starting_agents)
            + len(self._started_agents)
            + len(self._failed_live_agents)
        )

    def can_start_agent(self) -> bool:
        with self._lock:
            return self._occupied_count_unlocked() < self.max_workers

    def tracks_agent(self, agent_name: str) -> bool:
        """Return whether the pool owns a reserved, running, or live-failed agent."""
        with self._lock:
            return agent_name in (
                self._starting_agents | self._started_agents | self._failed_live_agents
            )

    def is_started(self, agent_name: str) -> bool:
        with self._lock:
            return agent_name in self._started_agents

    def is_starting(self, agent_name: str) -> bool:
        with self._lock:
            return agent_name in self._starting_agents

    def is_queued(self, agent_name: str) -> bool:
        with self._lock:
            return agent_name in self._waiting_queue

    def start_agent(self, agent_name: str) -> WorkerStartResult:
        """Reserve a slot and start, or enqueue atomically when at capacity."""
        # Registration is stable for the scheduler lifetime, so reject unknown
        # names before they can reserve capacity or enter the waiting queue.
        self.lifecycle_manager.get_agent(agent_name)
        with self._lock:
            if not self._accepting_starts:
                raise RuntimeError(
                    "Worker pool is stopping and cannot accept new starts."
                )
            if self.tracks_agent(agent_name):
                raise RuntimeError(f"Agent '{agent_name}' is already active.")
            if agent_name in self._waiting_queue:
                return WorkerStartResult(WorkerStartStatus.QUEUED)
            if self._occupied_count_unlocked() >= self.max_workers:
                self._waiting_queue.append(agent_name)
                self.logger.warning(
                    f"Max workers ({self.max_workers}) reached. "
                    f"Queueing agent '{agent_name}'"
                )
                return WorkerStartResult(WorkerStartStatus.QUEUED)
            self._starting_agents.add(agent_name)
            try:
                attempt = self.lifecycle_manager.prepare_start(agent_name)
            except Exception:
                self._starting_agents.discard(agent_name)
                raise

        try:
            result = self._start_reserved_agent(agent_name, attempt)
        except Exception:
            if not self.tracks_agent(agent_name):
                self._drain_waiting_queue()
            raise
        if result.status in {
            WorkerStartStatus.CANCELLED,
            WorkerStartStatus.FAILED_CLEAN,
        }:
            # Other callers may have queued work while startup was blocking.
            self._drain_waiting_queue()
        return result

    def _start_reserved_agent(
        self,
        agent_name: str,
        attempt: AgentStartAttempt,
    ) -> WorkerStartResult:
        """Run blocking startup outside the scheduler lock, then classify it."""
        try:
            lifecycle_result = self.lifecycle_manager.execute_start(
                agent_name,
                attempt,
            )
        except Exception:
            # Invariant/programming errors are exceptional, but the scheduler
            # must still never forget a concrete instance that may be alive.
            try:
                remains_live = self.lifecycle_manager.is_attempt_alive(
                    agent_name,
                    attempt,
                )
            except Exception:
                remains_live = True
            with self._lock:
                self._starting_agents.discard(agent_name)
                if remains_live:
                    self._failed_live_agents.add(agent_name)
            raise

        worker_result = self._classify_lifecycle_result(lifecycle_result)
        with self._lock:
            self._starting_agents.discard(agent_name)
            if lifecycle_result.status is LifecycleStartStatus.STARTED:
                self._started_agents.add(agent_name)
            elif lifecycle_result.status is LifecycleStartStatus.FAILED_LIVE:
                self._failed_live_agents.add(agent_name)
            occupied = self._occupied_count_unlocked()

        if worker_result.status is WorkerStartStatus.FAILED_LIVE:
            self.logger.critical(
                f"Agent '{agent_name}' failed startup but remains alive; "
                "its worker slot is quarantined."
            )
        elif worker_result.started:
            self.logger.info(
                f"Agent '{agent_name}' started "
                f"({occupied}/{self.max_workers} slots used)"
            )
        return worker_result

    @staticmethod
    def _classify_lifecycle_result(
        result: LifecycleStartResult,
    ) -> WorkerStartResult:
        status_map = {
            LifecycleStartStatus.STARTED: WorkerStartStatus.STARTED,
            LifecycleStartStatus.CANCELLED: WorkerStartStatus.CANCELLED,
            LifecycleStartStatus.FAILED_CLEAN: WorkerStartStatus.FAILED_CLEAN,
            LifecycleStartStatus.FAILED_LIVE: WorkerStartStatus.FAILED_LIVE,
        }
        return WorkerStartResult(status_map[result.status], result.reason)

    def on_agent_terminated(self, agent_name: str) -> None:
        """Release tracked capacity and schedule queued work."""
        with self._lock:
            tracked = self.tracks_agent(agent_name)
            self._starting_agents.discard(agent_name)
            self._started_agents.discard(agent_name)
            self._failed_live_agents.discard(agent_name)
            occupied = self._occupied_count_unlocked()

        if not tracked:
            self.logger.debug(
                f"Agent '{agent_name}' terminated without an owned worker slot."
            )
            return

        self.lifecycle_manager.mark_terminated(agent_name)
        self.logger.info(
            f"Agent '{agent_name}' terminated "
            f"({occupied}/{self.max_workers} slots used)"
        )
        self._drain_waiting_queue()

    def _reserve_next_queued(
        self,
    ) -> tuple[str, AgentStartAttempt] | None:
        with self._lock:
            while (
                self._waiting_queue
                and self._occupied_count_unlocked() < self.max_workers
            ):
                agent_name = self._waiting_queue.popleft()
                self._starting_agents.add(agent_name)
                try:
                    attempt = self.lifecycle_manager.prepare_start(agent_name)
                except Exception as error:
                    self._starting_agents.discard(agent_name)
                    self.logger.error(
                        f"Queued agent '{agent_name}' could not prepare startup: "
                        f"{error}"
                    )
                    continue
                return agent_name, attempt
            return None

    def _drain_waiting_queue(self) -> None:
        """Continue after clean failures; retain slots for live failures."""
        while True:
            reserved = self._reserve_next_queued()
            if reserved is None:
                return
            agent_name, attempt = reserved
            self.logger.info(f"Starting queued agent '{agent_name}'")
            try:
                result = self._start_reserved_agent(agent_name, attempt)
            except Exception as error:
                self.logger.error(
                    f"Queued agent '{agent_name}' raised during startup: {error}"
                )
                continue
            if result.status in {
                WorkerStartStatus.STARTED,
                WorkerStartStatus.FAILED_LIVE,
            }:
                return
            self.logger.error(
                f"Queued agent '{agent_name}' did not start "
                f"({result.status.value}); trying next."
            )

    def stop_agent(self, agent_name: str) -> None:
        """Cancel a queued request or stop an active lifecycle."""
        with self._lock:
            was_queued = agent_name in self._waiting_queue
            if was_queued:
                self._waiting_queue = deque(
                    name for name in self._waiting_queue if name != agent_name
                )
        self.lifecycle_manager.stop_agent(agent_name)

    def stop_all(self) -> None:
        """Cancel queued work and request stop without holding the pool lock."""
        with self._lock:
            self._accepting_starts = False
            self._waiting_queue.clear()
        self.lifecycle_manager.stop_all()

    def shutdown_all(self, timeout: float | None = None) -> list[str]:
        """Cancel queued work and block until every agent has terminated.

        Args:
            timeout: Overall budget in seconds for the cooperative wait.

        Returns:
            list[str]: Names of the agents that are still alive afterwards.
        """
        with self._lock:
            self._accepting_starts = False
            self._waiting_queue.clear()

        survivors = self.lifecycle_manager.shutdown_all(timeout=timeout)

        for agent in self.lifecycle_manager.get_all_agents():
            if agent.name in survivors:
                continue
            if self.tracks_agent(agent.name):
                self.on_agent_terminated(agent.name)

        return survivors

    @property
    def all_finished(self) -> bool:
        with self._lock:
            return self._occupied_count_unlocked() == 0 and not self._waiting_queue

    @property
    def queue_size(self) -> int:
        with self._lock:
            return len(self._waiting_queue)

    @property
    def running_count(self) -> int:
        """Return live running plus quarantined agents."""
        with self._lock:
            return len(self._started_agents) + len(self._failed_live_agents)

    def get_stats(self) -> dict:
        with self._lock:
            occupied = self._occupied_count_unlocked()
            return {
                "running": len(self._started_agents) + len(self._failed_live_agents),
                "starting": len(self._starting_agents),
                "queued": len(self._waiting_queue),
                "quarantined": len(self._failed_live_agents),
                "max_workers": self.max_workers,
                "capacity_used": f"{occupied}/{self.max_workers}",
                "started_agents": sorted(self._started_agents),
                "starting_agents": sorted(self._starting_agents),
                "quarantined_agents": sorted(self._failed_live_agents),
            }
