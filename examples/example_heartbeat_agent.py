"""
Example demonstrating the AgentHeartbeatTimerPlugin.

This example shows how to use the heartbeat plugin to send periodic
heartbeat messages to the orchestrator for monitoring purposes.
"""

import time

from PyOrchestrate.core.orchestrator import Orchestrator, RunMode
from PyOrchestrate.core.orchestrator.orchestrator import OrchestratorPlugin
from PyOrchestrate.core.agent import PeriodicProcessAgent
from PyOrchestrate.core.plugins.orchestrator_heartbeat import (
    OrchestratorHeartbeatPlugin,
    HeartbeatConfig,
)
from PyOrchestrate.core.plugins.heartbeat import AgentHeartbeatTimerPlugin


class CriticalAgent(PeriodicProcessAgent):
    """Agent that demonstrates heartbeat functionality."""

    class Config(PeriodicProcessAgent.Config):
        """Configuration for the CriticalAgent."""

        limit = 10
        execution_interval = 3.0  # Execute every 3 seconds

    config: Config

    def runner(self):
        """Main agent logic."""
        super().runner()

        # Simulate some work
        self.logger.info("CriticalAgent working...")

    def setup(self):
        """Setup method called when agent starts."""
        super().setup()
        self.logger.info("CriticalAgent setup complete")


if __name__ == "__main__":
    # Create orchestrator plugin with heartbeat
    orchestrator_plugin = OrchestratorPlugin(
        heartbeat=OrchestratorHeartbeatPlugin(
            config=HeartbeatConfig(
                enabled=True,
                agent_send_interval=2.0,  # Agents send heartbeat every 2 seconds
                agent_jitter=0.1,  # ±10% jitter to desynchronize
                timeout_multiplier=3.0,  # Timeout after 6 seconds (2.0 * 3.0)
                auto_inject=True,  # Auto-inject heartbeat plugin into all agents
            )
        )
    )

    # Create orchestrator with heartbeat plugin
    orchestrator = Orchestrator(
        plugin=orchestrator_plugin, config=Orchestrator.Config(run_mode=RunMode.DAEMON)
    )

    # Register heartbeat agent
    orchestrator.register_agent(CriticalAgent, "CriticalAgent")

    orchestrator.start()
    orchestrator.join()
