"""Unit tests for OrchestratorHeartbeatPlugin timeout detection."""

import unittest

from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator
from PyOrchestrate.core.plugins.heartbeat import OrchestratorHeartbeatPlugin


class TestHeartbeatTimeoutReporting(unittest.TestCase):
    """Test cases for heartbeat timeout detection and reporting."""

    def setUp(self):
        """Set up an orchestrator with a fast-timing heartbeat plugin."""
        self.heartbeat = OrchestratorHeartbeatPlugin(
            agent_send_interval=0.2,
            timeout_multiplier=1.0,
            check_interval=0.2,
        )
        self.orch = Orchestrator(
            config=Orchestrator.Config(
                enable_command_interface=False,  # Disable ZMQ in tests
            ),
            plugin=Orchestrator.Plugin(heartbeat=self.heartbeat),
            name="test_heartbeat_orchestrator",
        )

    def _simulate_timeout(self, agent_name: str = "ghost"):
        """Mark an agent as monitored with a heartbeat old enough to time out."""
        self.heartbeat._monitored_agents.add(agent_name)
        self.heartbeat._agent_last_heartbeat[agent_name] = 0.0
        self.heartbeat._check_heartbeat_timeouts()

    def test_timeout_recorded_in_event_store(self):
        """Test a detected timeout reaches the orchestrator event store."""
        self._simulate_timeout()

        events = self.orch.event_bus.event_store.last(
            n=10, event_name="AGENT_TIMEOUT"
        )

        self.assertEqual(len(events), 1)
        record = events[0]
        self.assertEqual(record.agent, "ghost")
        self.assertEqual(record.category, "heartbeat")
        self.assertEqual(record.severity, "ERROR")
        self.assertEqual(record.data["timeout_threshold"], "0.2s")

    def test_timeout_reported_once_per_agent(self):
        """Test a still-silent agent is not recorded again on the next check."""
        self._simulate_timeout()
        self.heartbeat._check_heartbeat_timeouts()

        events = self.orch.event_bus.event_store.last(
            n=10, event_name="AGENT_TIMEOUT"
        )

        self.assertEqual(len(events), 1)

    def test_timeout_reported_again_after_heartbeat_resumes(self):
        """Test an agent that recovers and goes silent again is recorded twice."""
        self._simulate_timeout()

        # A fresh heartbeat clears the timeout flag, then silence returns
        self.heartbeat._on_agent_heartbeat("ghost")
        self._simulate_timeout()

        events = self.orch.event_bus.event_store.last(
            n=10, event_name="AGENT_TIMEOUT"
        )

        self.assertEqual(len(events), 2)


if __name__ == "__main__":
    unittest.main()
