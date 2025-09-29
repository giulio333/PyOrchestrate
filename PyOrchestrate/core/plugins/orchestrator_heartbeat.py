"""
Orchestrator Heartbeat Plugin for PyOrchestrate.

This plugin provides heartbeat monitoring capabilities for the orchestrator, allowing it to
automatically inject heartbeat functionality into agents and monitor their health status.
"""

import time
import threading
from typing import Dict, Optional, Set, TYPE_CHECKING
from dataclasses import dataclass, field

from PyOrchestrate.core.plugins.heartbeat import AgentHeartbeatTimerPlugin
from PyOrchestrate.core.utilities.event import OrchestratorEvent

if TYPE_CHECKING:
    from PyOrchestrate.core.orchestrator import Orchestrator


@dataclass
class HeartbeatConfig:
    """
    Configuration for heartbeat monitoring.

    Attributes:
        enabled: Whether heartbeat monitoring is enabled
        agent_send_interval: Interval in seconds for agents to send heartbeats
        agent_jitter: Jitter factor for agent heartbeat intervals (0.0 to 1.0)
        timeout_multiplier: Multiplier for timeout detection (timeout = interval * multiplier)
        check_interval: How often to check for timeouts (seconds)
        auto_inject: Whether to automatically inject heartbeat plugins into agents
    """

    enabled: bool = True
    agent_send_interval: float = 30.0
    agent_jitter: float = 0.1
    timeout_multiplier: float = 3.0
    check_interval: float = 5.0
    auto_inject: bool = True


class OrchestratorHeartbeatPlugin:
    """
    Orchestrator plugin that manages heartbeat monitoring for all agents.

    This plugin:
    1. Automatically injects heartbeat plugins into registered agents (if auto_inject=True)
    2. Monitors incoming heartbeat messages from agents
    3. Detects agents that have stopped sending heartbeats (timeout detection)
    4. Provides status and health information for all monitored agents

    Example usage:
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
    """

    def __init__(self, config: Optional[HeartbeatConfig] = None):
        """
        Initialize the orchestrator heartbeat plugin.

        Args:
            config: Heartbeat configuration. If None, uses default configuration.
        """
        self.config = config or HeartbeatConfig()

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

    def set_owner(self, orchestrator: "Orchestrator"):
        """
        Set the orchestrator reference.

        Called by the orchestrator when the plugin is attached.

        Args:
            orchestrator: The orchestrator instance
        """
        self._orchestrator = orchestrator

    def initialize(self):
        """Initialize the heartbeat monitoring plugin."""
        if not self.config.enabled or self._initialized:
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

            # self._orchestrator.register_event(
            #     OrchestratorEvent.AGENT_TERMINATED, self._on_agent_terminated
            # )

            # Start monitoring thread
            self._start_monitoring_thread()

            if hasattr(self._orchestrator, "logger"):
                self._orchestrator.logger.info(
                    f"Heartbeat monitoring initialized: "
                    f"interval={self.config.agent_send_interval}s, "
                    f"timeout={self.config.agent_send_interval * self.config.timeout_multiplier}s"
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

        if self._orchestrator and hasattr(self._orchestrator, "logger"):
            self._orchestrator.logger.info("Heartbeat monitoring finalized")

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
                if self._orchestrator and hasattr(self._orchestrator, "logger"):
                    self._orchestrator.logger.error(
                        f"Error in heartbeat monitoring: {e}"
                    )

            # Wait for next check
            if self._stop_event.wait(timeout=self.config.check_interval):
                break

    def _check_heartbeat_timeouts(self):
        """Check for agents that have exceeded the heartbeat timeout."""
        current_time = time.time()
        timeout_threshold = (
            self.config.agent_send_interval * self.config.timeout_multiplier
        )

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
        if self._orchestrator and hasattr(self._orchestrator, "logger"):
            last_heartbeat = self._agent_last_heartbeat.get(agent_name, 0)
            time_since = time.time() - last_heartbeat

            self._orchestrator.logger.warning(
                f"Agent '{agent_name}' heartbeat timeout detected! "
                f"Last heartbeat: {time_since:.1f}s ago"
            )

            # Record event in event store if available
            if hasattr(self._orchestrator, "event_store"):
                self._orchestrator.event_store.record(
                    category="heartbeat",
                    event_name="AGENT_TIMEOUT",
                    agent=agent_name,
                    severity="ERROR",
                    data={
                        "time_since_last": f"{time_since:.1f}s",
                        "timeout_threshold": f"{self.config.agent_send_interval * self.config.timeout_multiplier:.1f}s",
                    },
                )

    def _on_agent_heartbeat(self, agent_name: str, **kwargs):
        """Handle incoming agent heartbeat events."""
        current_time = time.time()
        self._agent_last_heartbeat[agent_name] = current_time

        # Remove from timeout list if it was there
        self._timeout_detected.discard(agent_name)

        if self._orchestrator and hasattr(self._orchestrator, "logger"):
            self._orchestrator.logger.trace(
                f"Heartbeat received from agent '{agent_name}'"
            )

    def _on_agent_started(self, agent_name: str, **kwargs):
        """Handle agent started events."""
        self._monitored_agents.add(agent_name)
        self._agent_last_heartbeat[agent_name] = time.time()  # Initialize timestamp

        if self._orchestrator and hasattr(self._orchestrator, "logger"):
            self._orchestrator.logger.debug(
                f"Started monitoring heartbeat for agent '{agent_name}'"
            )

    def _on_agent_terminated(self, agent_name: str, **kwargs):
        """Handle agent terminated events."""
        self._monitored_agents.discard(agent_name)
        self._agent_last_heartbeat.pop(agent_name, None)
        self._timeout_detected.discard(agent_name)

        if self._orchestrator and hasattr(self._orchestrator, "logger"):
            self._orchestrator.logger.debug(
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
            "enabled": self.config.enabled,
            "auto_inject": self.config.auto_inject,
            "agent_send_interval": self.config.agent_send_interval,
            "timeout_threshold": self.config.agent_send_interval
            * self.config.timeout_multiplier,
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
        if not self.config.enabled or not self.config.auto_inject:
            return custom_plugin

        # Create a heartbeat plugin instance for the agent
        heartbeat_plugin = AgentHeartbeatTimerPlugin(
            enabled=True,
            send_every=self.config.agent_send_interval,
            jitter=self.config.agent_jitter,
        )

        # Check if agent already has a custom_plugin
        if custom_plugin is None:
            # Create a new plugin with the heartbeat
            from PyOrchestrate.core.base.base import BaseClassPlugin

            custom_plugin = BaseClassPlugin(heartbeat=heartbeat_plugin)
        else:
            # Add heartbeat to existing plugin
            # Check if the plugin already has a heartbeat attribute
            if (
                not hasattr(custom_plugin, "heartbeat")
                and not hasattr(custom_plugin, "_custom_attr")
                or "heartbeat" not in getattr(custom_plugin, "_custom_attr", {})
            ):
                # Add heartbeat to the existing plugin's _custom_attr
                if not hasattr(custom_plugin, "_custom_attr"):
                    custom_plugin._custom_attr = {}
                custom_plugin._custom_attr["heartbeat"] = heartbeat_plugin

        if self._orchestrator and hasattr(self._orchestrator, "logger"):
            self._orchestrator.logger.debug(
                f"Auto-injected heartbeat plugin into agent with interval={self.config.agent_send_interval}s"
            )

        return custom_plugin
