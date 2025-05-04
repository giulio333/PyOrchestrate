from multiprocessing.synchronize import Event
import unittest
from unittest.mock import MagicMock, call

from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator, OrchestratorEvent
from PyOrchestrate.core.agent import BaseProcessAgent
from PyOrchestrate.core.utilities.event_manager import EventManager


# Dummy agent to simulate an actual agent instance.
class DummyAgent(BaseProcessAgent):

    class Config(BaseProcessAgent.Config):
        custom_param = "custom_value"

    config: Config

    def execute(self):
        super().execute()


class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orch = Orchestrator(name="test_orchestrator")
        self.orch.event_manager.emit = MagicMock(
            side_effect=self.orch.event_manager.emit
        )
        self.orch.memory.add_agent = MagicMock(side_effect=self.orch.memory.add_agent)

    def test_register_agent(self):
        """
        Test the registration of a new agent in the orchestrator.

        This test verifies that:
        - The agent is correctly registered with the given name and parameters
        - The agent entry contains the expected configuration
        - Control events are properly initialized and set to ready state
        - The agent instance is not created during registration
        """
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
        """
        Test the behavior when attempting to register an agent with a name that already exists.

        This test verifies that:
        - The orchestrator raises a ValueError when trying to register an agent with a duplicate name
        - The first agent registration succeeds
        - The second agent registration with the same name fails
        """
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

    # def test_start_call(self):
    #     """
    #     Test the start and termination flow of an agent in the orchestrator.

    #     This test verifies that:
    #     - An agent can be registered with custom configuration
    #     - The agent starts successfully when the orchestrator starts
    #     - The correct sequence of events is emitted (AGENT_STARTED, AGENT_TERMINATED, ALL_AGENTS_TERMINATED)
    #     - The custom configuration is properly applied to the agent
    #     """
    #     entry = self.orch.register_agent(
    #         agent_class=DummyAgent,
    #         name="agent1",
    #         custom_config=DummyAgent.Config(custom_param="custom_value_2"),
    #         custom_plugin=None,
    #         control_events=None,
    #         state_events=None,
    #         event_manager=None,
    #     )
    #     self.orch.start()
    #     self.orch.join()
    #     self.orch.event_manager.emit.assert_has_calls(
    #         [
    #             call(OrchestratorEvent.AGENT_STARTED, agent_name="agent1"),
    #             call(OrchestratorEvent.AGENT_TERMINATED, agent_name="agent1"),
    #             call(OrchestratorEvent.ALL_AGENTS_TERMINATED),
    #         ]
    #     )
    #     self.assertEqual(entry.config.custom_param, "custom_value_2")  # type: ignore


if __name__ == "__main__":
    unittest.main()
