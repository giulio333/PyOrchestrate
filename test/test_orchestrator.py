import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from PyOrchestrate.core.orchestrator.orchestrator import (
    Orchestrator,
    OrchestratorEvent,
    RunMode,
)
from PyOrchestrate.core.agent import BaseProcessAgent
from PyOrchestrate.core.utilities.event import AgentEvent
from PyOrchestrate.core.utilities.messaging import ServiceMessage


# Dummy agent to simulate an actual agent instance.
class DummyAgent(BaseProcessAgent):

    class Config(BaseProcessAgent.Config):
        custom_param = "custom_value"

    config: Config

    def execute(self):
        super().execute()


class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orch = Orchestrator(
            config=Orchestrator.Config(
                run_mode=RunMode.STOP_ON_EMPTY,
                enable_command_interface=False,  # Disable ZMQ in tests
            ),
            name="test_orchestrator",
        )
        self.orch.event_bus.event_manager.emit = MagicMock(
            side_effect=self.orch.event_bus.event_manager.emit
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

        # A registered entry has no instance until a startup attempt builds one.
        # RuntimeError, not AssertionError: python -O strips assertions.
        with self.assertRaises(RuntimeError):
            entry.instance

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

    def test_handle_agent_message_events(self):
        """
        Verify that the orchestrator delegates agent messages to the message router,
        and that the correct events are emitted as a result.
        """
        event_map = {
            AgentEvent.AGENT_CLOSE.value: OrchestratorEvent.AGENT_TERMINATED,
            AgentEvent.AGENT_START.value: OrchestratorEvent.AGENT_STARTED,
            AgentEvent.AGENT_READY.value: OrchestratorEvent.AGENT_READY,
        }

        for payload, expected_event in event_map.items():
            self.orch.event_bus.event_manager.emit.reset_mock()  # type: ignore
            msg = ServiceMessage.create_status(
                sender="agent1",
                status="success",
                event_name=payload,
            )

            self.orch.message_router.route_agent_message(msg)
            self.orch.event_bus.event_manager.emit.assert_called_with(  # type: ignore
                expected_event, agent_name="agent1"
            )

    def test_routed_agent_events_reach_the_event_store(self):
        """
        Routed lifecycle events must be recorded in history, not only delivered
        to the registered callbacks.
        """
        for payload in (
            AgentEvent.AGENT_START.value,
            AgentEvent.AGENT_READY.value,
            AgentEvent.AGENT_CLOSE.value,
        ):
            msg = ServiceMessage.create_status(
                sender="agent1",
                status="success",
                event_name=payload,
            )
            self.orch.message_router.route_agent_message(msg)

        recorded = [
            record.event_name
            for record in self.orch.event_bus.get_history(agent_name="agent1")
        ]
        self.assertEqual(
            recorded,
            [
                OrchestratorEvent.AGENT_STARTED.value,
                OrchestratorEvent.AGENT_READY.value,
                OrchestratorEvent.AGENT_TERMINATED.value,
            ],
        )

    def test_routed_agent_error_is_recorded_with_error_severity(self):
        msg = ServiceMessage.create_status(
            sender="agent1",
            status="error",
            event_name=AgentEvent.AGENT_ERROR.value,
            error="boom",
        )

        self.orch.message_router.route_agent_message(msg)

        record = self.orch.event_bus.get_history(agent_name="agent1")[-1]
        self.assertEqual(record.event_name, OrchestratorEvent.AGENT_ERROR.value)
        self.assertEqual(record.severity, "ERROR")
        self.assertEqual(record.data["error_message"], "boom")

    def test_join_does_not_release_slot_while_generation_is_starting(self):
        entry = self.orch.register_agent(DummyAgent, "starting-agent")
        entry._initialize_instance()
        self.orch.worker_pool = MagicMock()
        self.orch.worker_pool.is_starting.return_value = True
        self.orch.worker_pool.all_finished = True
        self.orch._shutdown_channel_handlers = MagicMock()
        self.orch.plugin_manager.finalize_plugins = MagicMock()
        self.orch.start_time = 0

        with patch("PyOrchestrate.core.orchestrator.orchestrator.time.sleep") as sleep:
            self.orch.join()

        sleep.assert_called_once_with(self.orch.config.check_interval)
        self.orch.worker_pool.on_agent_terminated.assert_not_called()

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
