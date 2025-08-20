"""
Example demonstrating the complete heartbeat monitoring system.

This example shows how to use the OrchestratorHeartbeatPlugin to automatically
monitor agent health and inject heartbeat functionality into agents.
"""

import time

from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.orchestrator.orchestrator import OrchestratorPlugin
from PyOrchestrate.core.agent import PeriodicProcessAgent
from PyOrchestrate.core.plugins.orchestrator_heartbeat import (
    OrchestratorHeartbeatPlugin,
    HeartbeatConfig,
)
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
    # Create heartbeat configuration
    heartbeat_config = HeartbeatConfig(
        enabled=True,
        agent_send_interval=5.0,  # Agents send heartbeat every 5 seconds
        agent_jitter=0.1,  # 10% jitter to avoid thundering herd
        timeout_multiplier=2.5,  # Timeout after 12.5 seconds (5 * 2.5)
        check_interval=3.0,  # Check for timeouts every 3 seconds
        auto_inject=True,  # Automatically inject heartbeat into agents
    )

    # Create orchestrator heartbeat plugin
    # heartbeat_plugin = OrchestratorHeartbeatPlugin(config=heartbeat_config)

    # Create orchestrator plugin container
    # orchestrator_plugin = OrchestratorPlugin(heartbeat=heartbeat_plugin)

    # Create orchestrator with heartbeat monitoring
    # orchestrator = Orchestrator(plugin=orchestrator_plugin)

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
