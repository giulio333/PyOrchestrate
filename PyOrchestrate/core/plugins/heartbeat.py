"""
Plugin for agent heartbeat functionality.

This module provides a plugin that agents can use to send periodic heartbeat
messages to the orchestrator for monitoring purposes.
"""

import random
import threading
import time
from typing import Optional, TYPE_CHECKING

from PyOrchestrate.core.plugins.plugin_protocols import PluginProtocol
from PyOrchestrate.core.utilities.event import AgentEvent
from PyOrchestrate.core.utilities.messaging import ServiceMessage

if TYPE_CHECKING:
    from PyOrchestrate.core.agent.base_agent import BaseAgent


class AgentHeartbeatTimerPlugin(PluginProtocol):
    """
    Plugin that sends periodic heartbeat messages to the orchestrator.

    This plugin is designed to be used as an attribute in an agent's Plugin class.
    It automatically starts a background timer thread that sends AGENT_HEARTBEAT
    messages at regular intervals.

    Example usage:
        class MyAgent(PeriodicProcessAgent):
            class Plugin(PeriodicProcessAgent.Plugin):
                heartbeat = AgentHeartbeatTimerPlugin(
                    enabled=True,
                    send_every=30.0,
                    jitter=0.1
                )

            plugin: Plugin

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
        self._stop_event = threading.Event()
        self._initialized = False
        self._running = False

    def set_agent(self, agent):
        """
        Set the agent reference.

        Called by the plugin manager to provide access to the agent instance.

        Args:
            agent: The agent instance that owns this plugin
        """
        self._agent = agent
        # Debug log to verify the connection
        if hasattr(agent, "logger"):
            agent.logger.debug(f"Heartbeat plugin connected to agent: {agent.name}")

    def initialize(self):
        """Initialize the plugin. Called by the plugin manager."""
        if not self.enabled:
            return

        self._initialized = True

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
