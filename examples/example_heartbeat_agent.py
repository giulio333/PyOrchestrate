"""
Example demonstrating the OrchestratorHeartbeatPlugin.

This example shows how to use the heartbeat plugin to send periodic
heartbeat messages to the orchestrator for monitoring purposes.
"""

from PyOrchestrate.core.orchestrator import Orchestrator, RunMode
from PyOrchestrate.core.orchestrator.orchestrator import OrchestratorPlugin
from PyOrchestrate.core.agent import PeriodicProcessAgent
from PyOrchestrate.core.plugins.heartbeat import (
    OrchestratorHeartbeatPlugin,
)


class CriticalAgent(PeriodicProcessAgent):
    """Agent that demonstrates heartbeat functionality."""

    class Config(PeriodicProcessAgent.Config):
        """Configuration for the CriticalAgent."""

        limit = 10
        execution_interval = 3.0  # Execute every 3 seconds

    config: Config

    def setup(self):
        """Setup method called when agent starts."""
        super().setup()
        self.logger.info("CriticalAgent setup complete")

    def runner(self):
        """Main agent logic."""
        super().runner()

        # Simulate some work
        self.logger.info("CriticalAgent working...")

    def on_close(self):
        super().on_close()

        if self.plugin.heartbeat:
            stats = self.plugin.heartbeat.get_status()
            self.logger.info(f"Final Heartbeat Stats: {stats}")


class MyOrchestrator(Orchestrator):
    class Plugin(OrchestratorPlugin):
        heartbeat = OrchestratorHeartbeatPlugin(agent_send_interval=2)

    class Config(Orchestrator.Config):
        run_mode = RunMode.DAEMON


if __name__ == "__main__":

    # Create orchestrator with heartbeat plugin
    orchestrator = MyOrchestrator()

    # Register heartbeat agent
    orchestrator.register_agent(CriticalAgent, "CriticalAgent")

    orchestrator.start()
    orchestrator.join()
