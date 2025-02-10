import unittest
from unittest.mock import MagicMock, call
from PyOrchestrate.core.orchestrator.memory import AgentEntry

from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator, OrchestratorEvent
from PyOrchestrate.core.agent import BaseProcessAgent


# Dummy agent to simulate an actual agent instance.
class DummyAgent(BaseProcessAgent):

    class Config(BaseProcessAgent.Config):
        custom_param = "custom_value"

    config: Config

    def execute(self):
        super().execute()


class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orch = Orchestrator("test_orchestrator")
        # Override logger and event_manager for testing.
        # self.orch.logger = MagicMock()
        self.orch.event_manager.emit = MagicMock(
            side_effect=self.orch.event_manager.emit
        )
        self.orch.memory.add_agent = MagicMock(side_effect=self.orch.memory.add_agent)

    def test_register_agent_returns_entry(self):
        entry = self.orch.register_agent(
            agent_class=DummyAgent,
            name="agent1",
            custom_config=None,
            custom_plugin=None,
            control_events=None,
            state_events=None,
            event_manager=None,
            extra_param="value",
        )
        self.assertEqual(entry.name, "agent1")
        self.assertEqual(entry.kwargs["extra_param"], "value")

        with self.assertRaises(AssertionError):
            instance = entry.instance

    def test_register_agent_duplicate_name(self):
        self.orch.register_agent(
            agent_class=DummyAgent,
            name="agent1",
            custom_config=None,
            custom_plugin=None,
            control_events=None,
            state_events=None,
            event_manager=None,
        )
        with self.assertRaises(ValueError):
            self.orch.register_agent(
                agent_class=DummyAgent,
                name="agent1",
                custom_config=None,
                custom_plugin=None,
                control_events=None,
                state_events=None,
                event_manager=None,
            )

    def test_start_call(self):
        entry = self.orch.register_agent(
            agent_class=DummyAgent,
            name="agent1",
            custom_config=DummyAgent.Config(custom_param="custom_value_2"),
            custom_plugin=None,
            control_events=None,
            state_events=None,
            event_manager=None,
        )
        self.orch.start()
        self.orch.join()
        self.orch.event_manager.emit.assert_has_calls(
            [
                call(OrchestratorEvent.AGENT_STARTED, agent_name="agent1"),
                call(OrchestratorEvent.AGENT_TERMINATED, agent_name="agent1"),
                call(OrchestratorEvent.ALL_AGENTS_TERMINATED),
            ]
        )
        # self.assertEqual(entry.config.custom_param, "custom_value_2")  # type: ignore


if __name__ == "__main__":
    unittest.main()
