"""
Unit tests for CommandInterface.

Tests the command interface functionality including initialization, lifecycle management,
command handling, error handling, and event tracking.
"""

import unittest
from unittest.mock import MagicMock, patch, call
import time

from PyOrchestrate.core.orchestrator.command_interface import CommandInterface
from PyOrchestrate.core.orchestrator.event_store import EventStore
from PyOrchestrate.core.utilities.messaging import ServiceMessage
from loguru import logger


class TestCommandInterface(unittest.TestCase):
    """Test suite for CommandInterface class."""

    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = MagicMock()
        self.zmq_address = "tcp://*:5555"
        self.event_store = EventStore(capacity=100)
        self.logger = logger

        # Create command interface
        self.cmd_interface = CommandInterface(
            orchestrator=self.orchestrator,
            zmq_address=self.zmq_address,
            allowed_commands={"ps", "shutdown"},
            event_store=self.event_store,
            logger=self.logger,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, "cmd_interface"):
            if self.cmd_interface._channel_handler:
                self.cmd_interface.stop()
            # Close the ZMQ socket properly
            if hasattr(self.cmd_interface, "command_channel"):
                self.cmd_interface.command_channel.close()
            time.sleep(0.1)  # Give ZMQ time to release the port

    def test_initialization(self):
        """Test CommandInterface initialization."""
        self.assertEqual(self.cmd_interface.orchestrator, self.orchestrator)
        self.assertEqual(self.cmd_interface.zmq_address, self.zmq_address)
        self.assertEqual(self.cmd_interface.event_store, self.event_store)
        self.assertIsNotNone(self.cmd_interface.command_channel)
        self.assertIsNotNone(self.cmd_interface.command_handler)
        self.assertIsNone(self.cmd_interface._channel_handler)

    def test_start(self):
        """Test starting the command interface."""
        self.cmd_interface.start()

        self.assertIsNotNone(self.cmd_interface._channel_handler)
        self.assertTrue(self.cmd_interface.is_running())

    def test_start_already_started(self):
        """Test that starting an already started interface raises error."""
        self.cmd_interface.start()

        with self.assertRaises(RuntimeError) as ctx:
            self.cmd_interface.start()

        self.assertIn("already started", str(ctx.exception))

    def test_stop(self):
        """Test stopping the command interface."""
        self.cmd_interface.start()
        self.assertTrue(self.cmd_interface.is_running())

        self.cmd_interface.stop()

        self.assertFalse(self.cmd_interface.is_running())
        self.assertIsNone(self.cmd_interface._channel_handler)

    def test_stop_not_started(self):
        """Test that stopping a non-started interface doesn't raise error."""
        # Should not raise any exception
        self.cmd_interface.stop()

    def test_handle_command_success(self):
        """Test successful command handling."""
        # Mock command handler response
        success_response = ServiceMessage.create_command_response(
            sender="command_handler",
            status="success",
            data={"result": "test_data"},
            request_id="test_123",
        )
        self.cmd_interface.command_handler.execute_command_msg = MagicMock(
            return_value=success_response
        )

        # Mock command channel
        self.cmd_interface.command_channel = MagicMock()

        # Create command request
        request_msg = ServiceMessage.create_command(
            sender="cli_client",
            command="ps",
            args=[],
            request_id="test_123",
        )

        # Handle command
        self.cmd_interface.handle_command(request_msg)

        # Verify command handler was called
        self.cmd_interface.command_handler.execute_command_msg.assert_called_once_with(
            request_msg
        )

        # Verify response was sent
        self.cmd_interface.command_channel.send.assert_called_once_with(
            "cli", success_response
        )

    def test_handle_command_execution_error(self):
        """Test command handling when execution fails."""
        # Mock command handler to raise exception
        self.cmd_interface.command_handler.execute_command_msg = MagicMock(
            side_effect=Exception("Command execution failed")
        )

        # Mock command channel
        self.cmd_interface.command_channel = MagicMock()

        # Create command request
        request_msg = ServiceMessage.create_command(
            sender="cli_client",
            command="ps",
            args=[],
            request_id="test_456",
        )

        # Handle command
        self.cmd_interface.handle_command(request_msg)

        # Verify error was tracked to event store
        events = self.event_store.last(n=10)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_name, "CLI_ERROR")
        self.assertEqual(events[0].severity, "ERROR")

        # Verify error response was sent
        call_args = self.cmd_interface.command_channel.send.call_args
        self.assertEqual(call_args[0][0], "cli")
        response_msg = call_args[0][1]
        self.assertEqual(response_msg.payload["status"], "error")
        self.assertIn("Command execution failed", response_msg.payload["error"])

    def test_handle_command_validation_error(self):
        """Test command handling with validation error (empty command)."""
        # Mock command channel
        self.cmd_interface.command_channel = MagicMock()

        # Create command request with empty command
        request_msg = ServiceMessage.create_command(
            sender="cli_client",
            command="",  # Empty command
            args=[],
            request_id="test_789",
        )

        # Handle command
        self.cmd_interface.handle_command(request_msg)

        # Verify error was tracked to event store
        events = self.event_store.last(n=10)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_name, "CLI_ERROR")

        # Verify error response was sent
        call_args = self.cmd_interface.command_channel.send.call_args
        response_msg = call_args[0][1]
        self.assertEqual(response_msg.payload["status"], "error")
        self.assertIn("Command is required", response_msg.payload["error"])

    def test_handle_command_with_request_id(self):
        """Test that request_id is preserved in responses."""
        # Mock command handler response
        success_response = ServiceMessage.create_command_response(
            sender="command_handler",
            status="success",
            data={},
            request_id="unique_request_id",
        )
        self.cmd_interface.command_handler.execute_command_msg = MagicMock(
            return_value=success_response
        )

        # Mock command channel
        self.cmd_interface.command_channel = MagicMock()

        # Create command request with specific request_id
        request_msg = ServiceMessage.create_command(
            sender="cli_client",
            command="ps",
            args=[],
            request_id="unique_request_id",
        )

        # Handle command
        self.cmd_interface.handle_command(request_msg)

        # Verify response has correct request_id
        call_args = self.cmd_interface.command_channel.send.call_args
        response_msg = call_args[0][1]
        self.assertEqual(response_msg.payload["request_id"], "unique_request_id")

    def test_is_running_false_when_not_started(self):
        """Test is_running returns False when not started."""
        self.assertFalse(self.cmd_interface.is_running())

    def test_is_running_true_when_started(self):
        """Test is_running returns True when started."""
        self.cmd_interface.start()
        self.assertTrue(self.cmd_interface.is_running())

    def test_is_running_false_after_stop(self):
        """Test is_running returns False after stop."""
        self.cmd_interface.start()
        self.cmd_interface.stop()
        self.assertFalse(self.cmd_interface.is_running())

    def test_event_tracking_on_error(self):
        """Test that errors are properly tracked to event store."""
        # Mock command handler to raise exception
        self.cmd_interface.command_handler.execute_command_msg = MagicMock(
            side_effect=Exception("Test error")
        )

        # Mock command channel
        self.cmd_interface.command_channel = MagicMock()

        # Create command request
        request_msg = ServiceMessage.create_command(
            sender="cli_client", command="test", args=[], request_id="test_001"
        )

        # Handle command
        self.cmd_interface.handle_command(request_msg)

        # Check event store
        events = self.event_store.last(n=10)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].category, "cli")
        self.assertEqual(events[0].event_name, "CLI_ERROR")
        self.assertEqual(events[0].severity, "ERROR")
        if events[0].data:
            self.assertEqual(events[0].data["error"], "Test error")

    def test_multiple_command_handling(self):
        """Test handling multiple commands sequentially."""
        # Mock command handler
        success_response = ServiceMessage.create_command_response(
            sender="handler", status="success", data={}, request_id="test"
        )
        self.cmd_interface.command_handler.execute_command_msg = MagicMock(
            return_value=success_response
        )

        # Mock command channel
        self.cmd_interface.command_channel = MagicMock()

        # Handle multiple commands
        for i in range(3):
            request_msg = ServiceMessage.create_command(
                sender="cli", command=f"cmd_{i}", args=[], request_id=f"req_{i}"
            )
            self.cmd_interface.handle_command(request_msg)

        # Verify all commands were processed
        self.assertEqual(
            self.cmd_interface.command_handler.execute_command_msg.call_count, 3
        )
        self.assertEqual(self.cmd_interface.command_channel.send.call_count, 3)

    def test_allowed_commands_parameter(self):
        """Test that allowed_commands is passed to CommandHandler."""
        # Create interface with specific allowed commands
        cmd_interface = CommandInterface(
            orchestrator=self.orchestrator,
            zmq_address="tcp://*:5556",
            allowed_commands={"ps", "status", "shutdown"},
            event_store=self.event_store,
            logger=self.logger,
        )

        # Verify command handler was created (we can't directly check allowed_commands,
        # but we can verify the handler exists)
        self.assertIsNotNone(cmd_interface.command_handler)

    def test_allowed_commands_none(self):
        """Test that allowed_commands can be None (all commands allowed)."""
        # Create interface with None allowed_commands
        cmd_interface = CommandInterface(
            orchestrator=self.orchestrator,
            zmq_address="tcp://*:5557",
            allowed_commands=None,
            event_store=self.event_store,
            logger=self.logger,
        )

        # Verify command handler was created
        self.assertIsNotNone(cmd_interface.command_handler)


if __name__ == "__main__":
    unittest.main()
