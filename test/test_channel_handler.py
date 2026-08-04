"""Tests for ChannelHandler."""

import subprocess
import sys
import unittest
import time
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime

from PyOrchestrate.core.orchestrator import channel_handler as channel_handler_module
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


ORPHANED_HANDLER_SCRIPT = """
import time

from loguru import logger

from PyOrchestrate.core.orchestrator.channel_handler import ChannelHandler
from PyOrchestrate.core.utilities.messaging import MessageChannel

channel = MessageChannel("process")
handler = ChannelHandler(
    channel=channel,
    message_handler=lambda msg: None,
    name="OrphanHandler",
    logger=logger,
    poll_timeout=0.05,
)
handler.start()
time.sleep(0.2)
{teardown}
print("end of script")
"""

# Closing the reader is what the interpreter does to the queue while it
# finalizes; doing it on purpose reproduces the failure without the race.
CLOSE_THE_CHANNEL = "channel._queue._reader.close()\ntime.sleep(0.3)"


class TestChannelHandlerShutdown(unittest.TestCase):
    """A handler nobody stopped must not take the interpreter down with it."""

    def _start_handler(self, logger, poll_timeout=0.05):
        """Start a handler on a real process channel and return both."""
        channel = MessageChannel("process")
        handler = ChannelHandler(
            channel=channel,
            message_handler=MagicMock(),
            name="TestHandler",
            logger=logger,
            poll_timeout=poll_timeout,
        )
        handler.start()
        self.addCleanup(handler.stop, 1.0)
        time.sleep(0.1)
        return channel, handler

    def _run_script(self, teardown=""):
        """Run the orphaned-handler script in its own interpreter."""
        return subprocess.run(
            [sys.executable, "-c", ORPHANED_HANDLER_SCRIPT.format(teardown=teardown)],
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_closed_channel_ends_the_loop_without_logging_an_error(self):
        """A channel closed underneath the poll is a stop condition."""
        logger = MagicMock()
        channel, handler = self._start_handler(logger)

        channel._queue._reader.close()

        deadline = time.monotonic() + 5.0
        while handler.is_running() and time.monotonic() < deadline:
            time.sleep(0.05)

        self.assertFalse(handler.is_running())
        logger.error.assert_not_called()

    def test_a_running_handler_is_registered_for_the_atexit_backstop(self):
        """start() enlists the handler, stop() takes it off the list."""
        _, handler = self._start_handler(MagicMock())

        self.assertIn(handler, channel_handler_module._live_handlers)

        handler.stop(timeout=1.0)

        self.assertNotIn(handler, channel_handler_module._live_handlers)

    def test_nothing_is_logged_while_the_interpreter_finalizes(self):
        """Writing to stderr during finalization is what aborts the process."""
        logger = MagicMock()
        handler = ChannelHandler(
            channel=MagicMock(spec=MessageChannel),
            message_handler=MagicMock(),
            name="TestHandler",
            logger=logger,
        )

        with patch("sys.is_finalizing", return_value=True):
            handler._log("error", "boom")

        logger.error.assert_not_called()

    def test_orphaned_handler_survives_its_channel_closing_at_exit(self):
        """The scenario from the failing CI runs, in a real interpreter."""
        result = self._run_script(teardown=CLOSE_THE_CHANNEL)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("end of script", result.stdout)
        self.assertNotIn("Error in OrphanHandler", result.stderr)
        self.assertNotIn("Fatal Python error", result.stderr)

    def test_orphaned_handler_is_stopped_at_interpreter_exit(self):
        """The atexit backstop joins a handler whose stop() was never called."""
        result = self._run_script()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("end of script", result.stdout)
        self.assertNotIn("did not stop properly", result.stderr)
        self.assertNotIn("Fatal Python error", result.stderr)


if __name__ == "__main__":
    unittest.main()
