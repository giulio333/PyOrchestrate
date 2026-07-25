"""
Plugin for agent heartbeat functionality.

This module provides a plugin that agents can use to send periodic heartbeat
messages to the orchestrator for monitoring purposes.
"""

import random
import threading
import time
from typing import Optional, TYPE_CHECKING, Set, Dict, Optional

from PyOrchestrate.core.plugins.plugin_protocols import PluginProtocol
from PyOrchestrate.core.utilities.event import AgentEvent
from PyOrchestrate.core.utilities.messaging import ServiceMessage
from PyOrchestrate.core.utilities.event import OrchestratorEvent

if TYPE_CHECKING:
    from PyOrchestrate.core.agent.base_agent import BaseAgent
    from PyOrchestrate.core.orchestrator import Orchestrator


class OrchestratorHeartbeatPlugin(PluginProtocol):
    """
    Orchestrator plugin that manages heartbeat monitoring for all agents.

    This plugin:
    1. Automatically injects heartbeat plugins into registered agents (if auto_inject=True)
    2. Monitors incoming heartbeat messages from agents
    3. Detects agents that have stopped sending heartbeats (timeout detection)
    4. Provides status and health information for all monitored agents

    Example:
        ```python
        heartbeat_plugin = OrchestratorHeartbeatPlugin(
            config=HeartbeatConfig(
                agent_send_interval=10.0,
                timeout_multiplier=3.0,
                auto_inject=True
            )
        )

        orchestrator = Orchestrator(
            plugin=OrchestratorPlugin(heartbeat=heartbeat_plugin)
        )
        ```
    """

    def __init__(
        self,
        agent_send_interval: float = 30.0,
        agent_jitter: float = 0.1,
        timeout_multiplier: float = 3.0,
        check_interval: float = 5.0,
    ):
        """
        Initialize the orchestrator heartbeat plugin.

        Args:
            agent_send_interval: Expected interval (in seconds) between agent heartbeats
            agent_jitter: Jitter factor (0.0 to 1.0) for agent heartbeat intervals
            timeout_multiplier: Multiplier for timeout detection (e.g., 3.0 means timeout if no heartbeat in 3 * interval)
            check_interval: Interval (in seconds) to check for heartbeat timeouts
        """
        self.agent_send_interval = agent_send_interval
        self.agent_jitter = agent_jitter
        self.timeout_multiplier = timeout_multiplier
        self.check_interval = check_interval

        # Tracking data
        self._agent_last_heartbeat: Dict[str, float] = {}
        self._monitored_agents: Set[str] = set()
        self._timeout_detected: Set[str] = set()

        # Monitoring thread
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._initialized = False

        # Reference to orchestrator (set when plugin is attached)
        self._orchestrator: Optional["Orchestrator"] = None

    @property
    def orchestrator(self) -> "Orchestrator":
        """Get the orchestrator instance."""
        if self._orchestrator is None:
            raise ValueError("Orchestrator reference not set. Plugin not attached?")
        return self._orchestrator

    def set_owner(self, owner: "Orchestrator"):
        """
        Set the orchestrator reference.

        Called by the orchestrator when the plugin is attached.

        Args:
            orchestrator: The orchestrator instance
        """
        self._orchestrator = owner

    def initialize(self):
        """Initialize the heartbeat monitoring plugin."""
        if self._initialized:
            return

        self._initialized = True

        if self._orchestrator:
            # Register for heartbeat events
            self._orchestrator.register_event(
                OrchestratorEvent.AGENT_HEARTBEAT, self._on_agent_heartbeat
            )

            # Register for agent lifecycle events
            self._orchestrator.register_event(
                OrchestratorEvent.AGENT_STARTED, self._on_agent_started
            )

            self._orchestrator.register_event(
                OrchestratorEvent.AGENT_TERMINATED, self._on_agent_terminated
            )

            # Start monitoring thread
            self._start_monitoring_thread()

            self._orchestrator.logger.info(
                f"Heartbeat monitoring initialized: "
                f"interval={self.agent_send_interval}s, "
                f"timeout={self.agent_send_interval * self.timeout_multiplier}s"
            )

    def finalize(self):
        """Finalize the heartbeat monitoring plugin."""
        if not self._initialized:
            return

        # Stop monitoring thread
        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)

        self._initialized = False

        self.orchestrator.logger.info("Heartbeat monitoring finalized")

    def _start_monitoring_thread(self):
        """Start the heartbeat monitoring thread."""
        if self._monitor_thread is not None:
            return

        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True, name="HeartbeatMonitor"
        )
        self._stop_event.clear()
        self._monitor_thread.start()

    def _monitoring_loop(self):
        """Main monitoring loop that checks for heartbeat timeouts."""
        while not self._stop_event.is_set():
            try:
                self._check_heartbeat_timeouts()
            except Exception as e:
                self.orchestrator.logger.error(f"Error in heartbeat monitoring: {e}")

            # Wait for next check
            if self._stop_event.wait(timeout=self.check_interval):
                break

    def _check_heartbeat_timeouts(self):
        """Check for agents that have exceeded the heartbeat timeout."""
        current_time = time.time()
        timeout_threshold = self.agent_send_interval * self.timeout_multiplier

        newly_timeout_agents = set()

        for agent_name in self._monitored_agents.copy():
            last_heartbeat = self._agent_last_heartbeat.get(agent_name)

            if last_heartbeat is None:
                continue

            time_since_last = current_time - last_heartbeat

            # Check if agent has timed out
            if time_since_last > timeout_threshold:
                if agent_name not in self._timeout_detected:
                    newly_timeout_agents.add(agent_name)
                    self._timeout_detected.add(agent_name)

        # Report newly detected timeouts
        for agent_name in newly_timeout_agents:
            self._report_agent_timeout(agent_name)

    def _report_agent_timeout(self, agent_name: str):
        """Report that an agent has timed out."""
        last_heartbeat = self._agent_last_heartbeat.get(agent_name, 0)
        time_since = time.time() - last_heartbeat

        self.orchestrator.logger.warning(
            f"Agent '{agent_name}' heartbeat timeout detected! "
            f"Last heartbeat: {time_since:.1f}s ago"
        )

        # Record event in event store
        self.orchestrator.event_store.record(
            category="heartbeat",
            event_name="AGENT_TIMEOUT",
            agent=agent_name,
            severity="ERROR",
            data={
                "time_since_last": f"{time_since:.1f}s",
                "timeout_threshold": f"{self.agent_send_interval * self.timeout_multiplier:.1f}s",
            },
        )

    def _on_agent_heartbeat(self, agent_name: str, **kwargs):
        """Handle incoming agent heartbeat events."""
        current_time = time.time()
        self._agent_last_heartbeat[agent_name] = current_time

        # Remove from timeout list if it was there
        self._timeout_detected.discard(agent_name)

        self.orchestrator.logger.debug(f"Heartbeat received from agent '{agent_name}'")

    def _on_agent_started(self, agent_name: str, **kwargs):
        """Handle agent started events."""
        self._monitored_agents.add(agent_name)
        self._agent_last_heartbeat[agent_name] = time.time()  # Initialize timestamp

        self.orchestrator.logger.debug(
            f"Started monitoring heartbeat for agent '{agent_name}'"
        )

    def _on_agent_terminated(self, agent_name: str, **kwargs):
        """Handle agent terminated events."""
        self._monitored_agents.discard(agent_name)
        self._agent_last_heartbeat.pop(agent_name, None)
        self._timeout_detected.discard(agent_name)

        self.orchestrator.logger.debug(
            f"Stopped monitoring heartbeat for agent '{agent_name}'"
        )

    def get_status(self) -> dict:
        """
        Get the current status of heartbeat monitoring.

        Returns:
            Dictionary with monitoring status and agent health information
        """
        current_time = time.time()
        agent_status = {}

        for agent_name in self._monitored_agents:
            last_heartbeat = self._agent_last_heartbeat.get(agent_name)
            if last_heartbeat:
                time_since = current_time - last_heartbeat
                is_timeout = agent_name in self._timeout_detected

                agent_status[agent_name] = {
                    "last_heartbeat": last_heartbeat,
                    "time_since_last": f"{time_since:.1f}s",
                    "is_timeout": is_timeout,
                    "status": "timeout" if is_timeout else "healthy",
                }

        return {
            "agent_send_interval": self.agent_send_interval,
            "timeout_threshold": self.agent_send_interval * self.timeout_multiplier,
            "monitored_agents": len(self._monitored_agents),
            "timeout_agents": len(self._timeout_detected),
            "agents": agent_status,
        }

    def get_healthy_agents(self) -> Set[str]:
        """Get set of agents that are currently healthy (not timed out)."""
        return self._monitored_agents - self._timeout_detected

    def get_timeout_agents(self) -> Set[str]:
        """Get set of agents that have timed out."""
        return self._timeout_detected.copy()

    def inject_agent_heartbeat_plugin(self, custom_plugin):
        """
        Inject heartbeat plugin configuration into agent custom_plugin if auto_inject is enabled.

        Args:
            custom_plugin: The custom_plugin object to modify or None

        Returns:
            Modified custom_plugin with heartbeat plugin injected if auto_inject is enabled
        """
        # Create a heartbeat plugin instance for the agent
        heartbeat_plugin = AgentHeartbeatTimerPlugin(
            enabled=True,
            send_every=self.agent_send_interval,
            jitter=self.agent_jitter,
        )

        # TODO: don't override custom_plugin if already exists
        if custom_plugin is not None:
            self.orchestrator.logger.warning(
                "Overriding existing custom_plugin when auto-injecting heartbeat plugin"
            )

        from PyOrchestrate.core.agent.base_agent import AgentPlugin

        custom_plugin = AgentPlugin(heartbeat=heartbeat_plugin)

        self.orchestrator.logger.debug(
            f"Auto-injected heartbeat plugin into agent with interval={self.agent_send_interval}s"
        )

        return custom_plugin


class AgentHeartbeatTimerPlugin(PluginProtocol):
    """
    Plugin that sends periodic heartbeat messages to the orchestrator.

    This plugin is designed to be used as an attribute in an agent's Plugin class.
    It automatically starts a background timer thread that sends AGENT_HEARTBEAT
    messages at regular intervals.

    Example:
        ```python
        class MyAgent(PeriodicProcessAgent):
            class Plugin(PeriodicProcessAgent.Plugin):
                heartbeat = AgentHeartbeatTimerPlugin(
                    enabled=True,
                    send_every=30.0,
                    jitter=0.1
                )

            plugin: Plugin
        ```

    Attributes:
        enabled: Whether the heartbeat is enabled
        send_every: Interval in seconds between heartbeats
        jitter: Random variation added to the interval (0.0 to 1.0)
    """

    def __init__(
        self, enabled: bool = True, send_every: float = 30.0, jitter: float = 0.1
    ):
        """
        Initialize the heartbeat plugin.

        Args:
            enabled: Whether to enable heartbeat sending
            send_every: Base interval in seconds between heartbeats
            jitter: Random jitter factor (0.0 to 1.0) to add to interval
        """
        self.enabled = enabled
        self.send_every = send_every
        self.jitter = max(0.0, min(1.0, jitter))  # Clamp between 0 and 1

        self._agent: Optional[BaseAgent] = None  # Reference to the owning agent

        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event: Optional[threading.Event] = None
        self._initialized = False
        self._running = False

    def set_owner(self, owner):
        """
        Set the owner (agent) reference.

        Called by the plugin manager to provide access to the owner instance.

        Args:
            owner: The agent instance that owns this plugin
        """
        self._agent = owner
        owner.logger.debug(f"Heartbeat plugin connected to owner: {owner.name}")

    def initialize(self):
        """Initialize the plugin. Called by the plugin manager."""
        if not self.enabled:
            return

        self._initialized = True

        self._stop_event = threading.Event()

        # Start the heartbeat timer thread
        if self._timer_thread is None:
            self._timer_thread = threading.Thread(
                target=self._heartbeat_loop,
                daemon=True,
                name=f"HeartbeatTimer-{getattr(self._agent, 'name', 'Unknown')}",
            )
            self._stop_event.clear()
            self._timer_thread.start()
            self._running = True

    def finalize(self):
        """Finalize the plugin. Called by the plugin manager."""
        if not self.enabled or not self._initialized:
            return

        # Stop the timer thread
        if self._stop_event is not None:
            self._stop_event.set()
        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=1.0)

        self._running = False
        self._initialized = False

    def _heartbeat_loop(self):
        """
        Main loop for the heartbeat timer thread.

        Sends heartbeat messages at regular intervals with jitter.
        """
        if self._stop_event is None:
            return

        while not self._stop_event.is_set():
            # Calculate next interval with jitter
            base_interval = self.send_every
            jitter_amount = base_interval * self.jitter * random.random()
            actual_interval = base_interval + jitter_amount

            # Wait for the interval or stop event
            if self._stop_event.wait(timeout=actual_interval):
                break  # Stop event was set

            # Send heartbeat if we have an agent reference
            if self._agent is not None:
                self._send_heartbeat()

    def _send_heartbeat(self):
        """Send a heartbeat message to the orchestrator."""
        assert self._agent is not None

        try:
            # Create heartbeat service message
            heartbeat_message = ServiceMessage.create_status(
                sender=self._agent.name,
                status="success",
                event_name=AgentEvent.AGENT_HEARTBEAT.value,
            )

            # Send through agent's send_message method
            self._agent.send_message(heartbeat_message)

        except Exception as e:
            # Log error but don't crash the heartbeat thread
            if hasattr(self._agent, "logger"):
                self._agent.logger.error(f"Failed to send heartbeat: {e}")

    def get_status(self) -> dict:
        """
        Get the current status of the heartbeat plugin.

        Returns:
            Dictionary with plugin status information
        """
        agent_name = None
        if self._agent is not None:
            agent_name = getattr(self._agent, "name", None)

        return {
            "enabled": self.enabled,
            "send_every": self.send_every,
            "jitter": self.jitter,
            "initialized": self._initialized,
            "running": self._running,
            "agent_name": agent_name,
        }
