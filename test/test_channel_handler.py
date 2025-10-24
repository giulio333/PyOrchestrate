"""Tests for ChannelHandler."""

import unittest
import time
from unittest.mock import MagicMock, Mock
from datetime import datetime

from PyOrchestrate.core.orchestrator.channel_handler import ChannelHandler
from PyOrchestrate.core.utilities.messaging import MessageChannel, ServiceMessage


class TestChannelHandler(unittest.TestCase):
    """Test suite for ChannelHandler class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_channel = MagicMock(spec=MessageChannel)
        self.mock_handler = MagicMock()
        self.mock_logger = MagicMock()

    def tearDown(self):
        """Clean up after tests."""
        pass

    def test_initialization(self):
        """Test ChannelHandler initialization."""
        handler = ChannelHandler(
            channel=self.mock_channel,
            message_handler=self.mock_handler,
            name="TestHandler",
            logger=self.mock_logger,
            poll_timeout=0.5,
        )

        self.assertEqual(handler.channel, self.mock_channel)
        self.assertEqual(handler.message_handler, self.mock_handler)
        self.assertEqual(handler.name, "TestHandler")
        self.assertEqual(handler.logger, self.mock_logger)
        self.assertEqual(handler.poll_timeout, 0.5)
        self.assertFalse(handler.is_running())

    def test_start_handler(self):
        """Test starting the channel handler."""
        handler = ChannelHandler(
            channel=self.mock_channel,
            message_handler=self.mock_handler,
            name="TestHandler",
            logger=self.mock_logger,
            poll_timeout=0.1,
        )

        # Configure mock to return None (no messages)
        self.mock_channel.receive.return_value = None

        handler.start()

        # Give thread time to start
        time.sleep(0.2)

        self.assertTrue(handler.is_running())
        self.mock_logger.debug.assert_called_with("TestHandler started successfully")

        # Stop handler
        handler.stop(timeout=1.0)
        self.assertFalse(handler.is_running())

    def test_start_already_running(self):
        """Test starting an already running handler logs a warning."""
        handler = ChannelHandler(
            channel=self.mock_channel,
            message_handler=self.mock_handler,
            name="TestHandler",
            logger=self.mock_logger,
            poll_timeout=0.1,
        )

        self.mock_channel.receive.return_value = None

        handler.start()
        time.sleep(0.1)

        # Try to start again
        handler.start()

        self.mock_logger.warning.assert_called_with("TestHandler already running")

        handler.stop(timeout=1.0)

    def test_message_processing(self):
        """Test that messages are correctly processed."""
        test_msg = ServiceMessage(
            sender="test_agent",
            type="STATUS",
            payload={"event": "test_event"},
            timestamp=datetime.now(),
        )

        # Configure mock to return a message once, then None
        self.mock_channel.receive.side_effect = [test_msg, None, None, None]

        handler = ChannelHandler(
            channel=self.mock_channel,
            message_handler=self.mock_handler,
            name="TestHandler",
            logger=self.mock_logger,
            poll_timeout=0.05,
        )

        handler.start()

        # Wait for message to be processed
        time.sleep(0.3)

        # Verify message handler was called with the message
        self.mock_handler.assert_called()
        call_args = self.mock_handler.call_args[0]
        self.assertEqual(call_args[0].sender, "test_agent")
        self.assertEqual(call_args[0].type, "STATUS")

        handler.stop(timeout=1.0)

    def test_stop_handler(self):
        """Test stopping the channel handler."""
        handler = ChannelHandler(
            channel=self.mock_channel,
            message_handler=self.mock_handler,
            name="TestHandler",
            logger=self.mock_logger,
            poll_timeout=0.1,
        )

        self.mock_channel.receive.return_value = None

        handler.start()
        time.sleep(0.1)

        self.assertTrue(handler.is_running())

        handler.stop(timeout=1.0)

        self.assertFalse(handler.is_running())
        self.mock_logger.trace.assert_called_with("TestHandler stopped successfully")

    def test_stop_not_running(self):
        """Test stopping a handler that is not running."""
        handler = ChannelHandler(
            channel=self.mock_channel,
            message_handler=self.mock_handler,
            name="TestHandler",
            logger=self.mock_logger,
            poll_timeout=0.1,
        )

        # Stop without starting
        handler.stop(timeout=1.0)

        # Should not raise an error
        self.assertFalse(handler.is_running())

    def test_exception_handling(self):
        """Test that exceptions in message handler are caught and logged."""

        def failing_handler(msg):
            raise ValueError("Test error")

        self.mock_channel.receive.side_effect = [
            ServiceMessage(
                sender="test",
                type="STATUS",
                payload={},
                timestamp=datetime.now(),
            ),
            None,
            None,
        ]

        handler = ChannelHandler(
            channel=self.mock_channel,
            message_handler=failing_handler,
            name="TestHandler",
            logger=self.mock_logger,
            poll_timeout=0.05,
        )

        handler.start()
        time.sleep(0.3)

        # Verify error was logged
        self.mock_logger.error.assert_called()
        error_call = self.mock_logger.error.call_args[0][0]
        self.assertIn("Error in TestHandler", error_call)

        handler.stop(timeout=1.0)

    def test_multiple_messages(self):
        """Test processing multiple messages in sequence."""
        messages = [
            ServiceMessage(
                sender=f"agent_{i}",
                type="STATUS",
                payload={"count": i},
                timestamp=datetime.now(),
            )
            for i in range(3)
        ]

        # Return messages then None
        self.mock_channel.receive.side_effect = messages + [None] * 5

        handler = ChannelHandler(
            channel=self.mock_channel,
            message_handler=self.mock_handler,
            name="TestHandler",
            logger=self.mock_logger,
            poll_timeout=0.05,
        )

        handler.start()
        time.sleep(0.5)

        # Verify all messages were processed
        self.assertEqual(self.mock_handler.call_count, 3)

        handler.stop(timeout=1.0)

    def test_poll_timeout_respected(self):
        """Test that poll timeout is used correctly."""
        handler = ChannelHandler(
            channel=self.mock_channel,
            message_handler=self.mock_handler,
            name="TestHandler",
            logger=self.mock_logger,
            poll_timeout=0.5,
        )

        self.mock_channel.receive.return_value = None

        handler.start()
        time.sleep(0.2)

        # Verify receive was called with correct timeout
        self.mock_channel.receive.assert_called_with(timeout=0.5)

        handler.stop(timeout=1.0)

    def test_handler_without_logger(self):
        """Test handler works without a logger."""
        handler = ChannelHandler(
            channel=self.mock_channel,
            message_handler=self.mock_handler,
            name="TestHandler",
            logger=None,  # No logger
            poll_timeout=0.1,
        )

        self.mock_channel.receive.return_value = None

        handler.start()
        time.sleep(0.2)

        self.assertTrue(handler.is_running())

        handler.stop(timeout=1.0)
        self.assertFalse(handler.is_running())


if __name__ == "__main__":
    unittest.main()
