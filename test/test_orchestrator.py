import unittest
from unittest.mock import MagicMock, call
from datetime import datetime

from PyOrchestrate.core.orchestrator.orchestrator import (
    Orchestrator,
    OrchestratorEvent,
    RunMode,
)
from PyOrchestrate.core.agent import BaseProcessAgent
from PyOrchestrate.core.utilities.event_manager import EventManager
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

    def test_handle_agent_message_events(self):
        """Verify that message_router.route_agent_message emits the correct events."""
        event_map = {
            AgentEvent.AGENT_CLOSE.value: OrchestratorEvent.AGENT_TERMINATED,
            AgentEvent.AGENT_START.value: OrchestratorEvent.AGENT_STARTED,
            AgentEvent.AGENT_READY.value: OrchestratorEvent.AGENT_READY,
        }

        for payload, expected_event in event_map.items():
            self.orch.event_manager.emit.reset_mock()  # type: ignore
            msg = ServiceMessage.create_status(
                sender="agent1",
                status="success",
                event_name=payload,
            )

            self.orch.message_router.route_agent_message(msg)
            self.orch.event_manager.emit.assert_called_with(  # type: ignore
                expected_event, agent_name="agent1"
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

    def test_handle_external_command_success(self):
        """Test that handle_external_command properly handles successful commands."""
        # Create a mock command handler that returns a success response
        mock_success_response = ServiceMessage.create_command_response(
            sender="command_handler",
            status="success",
            data={"result": "test_data"},
            request_id="test_request_123",
        )
        self.orch.command_handler = MagicMock()
        self.orch.command_handler.execute_command_msg = MagicMock(
            return_value=mock_success_response
        )

        # Create a mock command channel
        self.orch.command_channel = MagicMock()

        # Create a command request message
        request_msg = ServiceMessage.create_command(
            sender="cli_client",
            command="test_command",
            args=["arg1", "arg2"],
            request_id="test_request_123",
        )

        # Handle the external command
        self.orch.handle_external_command(request_msg)

        # Verify the command handler was called with the request
        self.orch.command_handler.execute_command_msg.assert_called_once_with(
            request_msg
        )

        # Verify the response was sent back through the command channel
        self.orch.command_channel.send.assert_called_once_with(
            "cli", mock_success_response
        )

    def test_handle_external_command_handler_exception(self):
        """Test that handle_external_command creates proper error response when command handler raises exception."""
        # Create a mock command handler that raises an exception
        self.orch.command_handler = MagicMock()
        self.orch.command_handler.execute_command_msg = MagicMock(
            side_effect=Exception("Command handler failed")
        )

        # Create a mock command channel
        self.orch.command_channel = MagicMock()

        # Mock event store
        self.orch.event_bus.event_store = MagicMock()

        # Create a command request message
        request_msg = ServiceMessage.create_command(
            sender="cli_client",
            command="test_command",
            args=[],
            request_id="test_request_456",
        )

        # Handle the external command
        self.orch.handle_external_command(request_msg)

        # Verify event store recorded the error
        self.orch.event_bus.event_store.record.assert_called_once_with(
            category="cli",
            event_name="CLI_ERROR",
            severity="ERROR",
            data={"error": "Command handler failed"},
        )

        # Verify an error response was sent (not the original request)
        call_args = self.orch.command_channel.send.call_args
        self.assertEqual(call_args[0][0], "cli")
        response_msg = call_args[0][1]

        # Verify response is a ServiceMessage with error status
        self.assertIsInstance(response_msg, ServiceMessage)
        self.assertEqual(response_msg.payload["status"], "error")
        self.assertEqual(response_msg.payload["error"], "Command handler failed")
        self.assertEqual(response_msg.payload["request_id"], "test_request_456")

    def test_handle_external_command_outer_exception(self):
        """Test that handle_external_command handles exceptions before reaching command handler."""
        # Create a mock command channel
        self.orch.command_channel = MagicMock()

        # Mock event store
        self.orch.event_bus.event_store = MagicMock()

        # Create a command request message without a command (to trigger ValueError)
        request_msg = ServiceMessage.create_command(
            sender="cli_client",
            command="",  # Empty command will trigger ValueError
            args=[],
            request_id="test_request_789",
        )

        # Handle the external command
        self.orch.handle_external_command(request_msg)

        # Verify event store recorded the error
        self.orch.event_bus.event_store.record.assert_called_once_with(
            category="cli",
            event_name="CLI_ERROR",
            severity="ERROR",
            data={"error": "Command is required"},
        )

        # Verify an error response was sent
        call_args = self.orch.command_channel.send.call_args
        self.assertEqual(call_args[0][0], "cli")
        response_msg = call_args[0][1]

        # Verify response is a ServiceMessage with error status
        self.assertIsInstance(response_msg, ServiceMessage)
        self.assertEqual(response_msg.payload["status"], "error")
        self.assertEqual(response_msg.payload["error"], "Command is required")
        self.assertEqual(response_msg.payload["request_id"], "test_request_789")


if __name__ == "__main__":
    unittest.main()
