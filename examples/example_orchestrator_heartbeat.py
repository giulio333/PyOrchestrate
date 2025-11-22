"""
Example demonstrating the complete heartbeat monitoring system.

This example shows how to use the OrchestratorHeartbeatPlugin to automatically
monitor agent health and inject heartbeat functionality into agents.
"""

import time

from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import PeriodicProcessAgent
from PyOrchestrate.core.plugins.heartbeat import AgentHeartbeatTimerPlugin


class TestAgent(PeriodicProcessAgent):
    """Test agent for heartbeat monitoring."""

    class Config(PeriodicProcessAgent.Config):
        """Configuration for the TestAgent."""

        limit = 15
        execution_interval = 2.0  # Execute every 2 seconds
        counter: int = 1

    config: Config

    def runner(self):
        """Main agent logic."""
        super().runner()

        # Simulate some work
        self.logger.info(
            f"TestAgent {self.name} working... (iteration {self.config.counter})"
        )

        # Increment counter
        self.config.counter += 1


if __name__ == "__main__":
    orchestrator = Orchestrator()

    # Register multiple test agents
    orchestrator.register_agent(
        TestAgent,
        "TestAgent1",
        custom_plugin=TestAgent.Plugin(
            p=AgentHeartbeatTimerPlugin(enabled=True, send_every=2)
        ),
    )
    orchestrator.register_agent(
        TestAgent,
        "TestAgent2",
        custom_plugin=TestAgent.Plugin(
            p=AgentHeartbeatTimerPlugin(enabled=True, send_every=2)
        ),
    )
    orchestrator.register_agent(
        TestAgent,
        "TestAgent3",
        custom_plugin=TestAgent.Plugin(
            p=AgentHeartbeatTimerPlugin(enabled=True, send_every=2)
        ),
    )

    try:
        # Start all agents
        orchestrator.start()

        orchestrator.join()

    finally:
        # Stop the orchestrator
        print("\n🛑 Stopping system...")
