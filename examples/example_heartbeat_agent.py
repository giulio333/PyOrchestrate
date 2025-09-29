"""
Example demonstrating the AgentHeartbeatTimerPlugin.

This example shows how to use the heartbeat plugin to send periodic
heartbeat messages to the orchestrator for monitoring purposes.
"""

import time

from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import PeriodicProcessAgent
from PyOrchestrate.core.plugins.heartbeat import AgentHeartbeatTimerPlugin


class HeartbeatAgent(PeriodicProcessAgent):
    """Agent that demonstrates heartbeat functionality."""

    class Config(PeriodicProcessAgent.Config):
        """Configuration for the HeartbeatAgent."""

        limit = 10
        execution_interval = 3.0  # Execute every 3 seconds

    class Plugin(PeriodicProcessAgent.Plugin):
        """Plugin configuration for the HeartbeatAgent."""

        # Heartbeat plugin sends a heartbeat every 2 seconds with 10% jitter
        heartbeat = AgentHeartbeatTimerPlugin(
            enabled=True,
            send_every=2.0,  # Send heartbeat every 2 seconds
            jitter=0.1,  # ±10% jitter to desynchronize
        )

    config: Config
    plugin: Plugin

    def runner(self):
        """Main agent logic."""
        super().runner()

        # Simulate some work
        self.logger.info("HeartbeatAgent working...")

        # Check heartbeat plugin status
        heartbeat_status = self.plugin.heartbeat.get_status()
        self.logger.info(
            f"Heartbeat status: running={heartbeat_status['running']}, agent_name={heartbeat_status['agent_name']}"
        )

    def setup(self):
        """Setup method called when agent starts."""
        super().setup()
        self.logger.info("HeartbeatAgent setup complete")

        # Log heartbeat plugin configuration
        status = self.plugin.heartbeat.get_status()
        self.logger.info(f"Heartbeat plugin configured: {status}")


if __name__ == "__main__":
    orchestrator = Orchestrator()

    # Register heartbeat agent
    orchestrator.register_agent(HeartbeatAgent, "HeartbeatAgent")

    orchestrator.start()
    orchestrator.join()
