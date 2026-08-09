"""Unit tests for OrchestratorHeartbeatPlugin timeout detection."""

import unittest

from PyOrchestrate.core.agent import PeriodicThreadAgent
from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator
from PyOrchestrate.core.plugins.heartbeat import (
    AgentHeartbeatTimerPlugin,
    OrchestratorHeartbeatPlugin,
)
from PyOrchestrate.core.plugins.plugin_protocols import PluginProtocol


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

        events = self.orch.event_bus.event_store.last(n=10, event_name="AGENT_TIMEOUT")

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

        events = self.orch.event_bus.event_store.last(n=10, event_name="AGENT_TIMEOUT")

        self.assertEqual(len(events), 1)

    def test_timeout_reported_again_after_heartbeat_resumes(self):
        """Test an agent that recovers and goes silent again is recorded twice."""
        self._simulate_timeout()

        # A fresh heartbeat clears the timeout flag, then silence returns
        self.heartbeat._on_agent_heartbeat("ghost")
        self._simulate_timeout()

        events = self.orch.event_bus.event_store.last(n=10, event_name="AGENT_TIMEOUT")

        self.assertEqual(len(events), 2)


class MarkerPlugin(PluginProtocol):
    """Minimal plugin standing in for one an agent declares itself."""

    def __init__(self):
        self.owner = None

    def set_owner(self, owner):
        self.owner = owner

    def initialize(self):
        pass

    def finalize(self):
        pass


class PluggedAgent(PeriodicThreadAgent):
    """Agent that declares a plugin of its own on its inner Plugin class."""

    class Config(PeriodicThreadAgent.Config):
        execution_interval = 0.05
        limit = 1

    class Plugin(PeriodicThreadAgent.Plugin):
        marker = MarkerPlugin()

    config: Config
    plugin: Plugin

    def runner(self):
        pass


class TestHeartbeatInjectionKeepsAgentPlugins(unittest.TestCase):
    """Test auto-injection adds a heartbeat without dropping the agent's plugins."""

    def setUp(self):
        """Set up an orchestrator whose heartbeat plugin auto-injects."""
        self.orch = Orchestrator(
            config=Orchestrator.Config(enable_command_interface=False),
            plugin=Orchestrator.Plugin(heartbeat=OrchestratorHeartbeatPlugin()),
            name="test_heartbeat_injection",
        )

    def _plugin_names(self, entry) -> set[str]:
        """Return the plugins the concrete instance would manage."""
        entry._initialize_instance()
        instance = entry.instance
        return {name for name, _ in instance.plugin_manager._extract_plugin_instances()}

    def test_agent_declared_plugin_survives_injection(self):
        """Test a plugin on the agent's Plugin class is not replaced."""
        entry = self.orch.register_agent(PluggedAgent, "plugged")

        names = self._plugin_names(entry)

        self.assertIn("marker", names)
        self.assertIn("heartbeat", names)

    def test_registration_plugin_survives_injection(self):
        """Test a container passed at registration keeps its own plugins."""
        container = PluggedAgent.Plugin()

        entry = self.orch.register_agent(
            PluggedAgent, "explicit", custom_plugin=container
        )

        names = self._plugin_names(entry)
        self.assertIn("marker", names)
        self.assertIn("heartbeat", names)

    def test_agent_declared_heartbeat_is_not_overwritten(self):
        """Test an agent configuring its own heartbeat keeps that instance."""
        own = AgentHeartbeatTimerPlugin(enabled=True, send_every=1.5)

        entry = self.orch.register_agent(
            PluggedAgent,
            "own_heartbeat",
            custom_plugin=PluggedAgent.Plugin(heartbeat=own),
        )
        entry._initialize_instance()

        self.assertIs(entry.instance.plugin.heartbeat, own)


if __name__ == "__main__":
    unittest.main()
