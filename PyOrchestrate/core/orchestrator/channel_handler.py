"""
Channel Handler Module

This module provides the ChannelHandler class for managing message channel
communication in separate threads, encapsulating thread lifecycle management.
"""

import threading
from typing import Callable, Optional

from PyOrchestrate.core.utilities.messaging import MessageChannel, ServiceMessage


class ChannelHandler:
    """
    Handles message channel communication in a separate thread.

    Encapsulates thread lifecycle management for message processing,
    providing a clean interface for starting, stopping, and handling
    messages from a MessageChannel.

    This class follows the Single Responsibility Principle by managing
    only the thread lifecycle and message polling, delegating message
    processing to a provided callback function.

    Attributes:
        channel (MessageChannel): The message channel to monitor.
        message_handler (Callable): Callback function to process received messages.
        name (str): Thread name for identification and logging.
        logger: Logger instance for debugging and error tracking.
        poll_timeout (float): Timeout for channel polling in seconds.

    Example:
        >>> # Create a handler for agent messages
        >>> handler = ChannelHandler(
        ...     channel=msg_channel,
        ...     message_handler=orchestrator.handle_agent_message,
        ...     name="AgentMessageHandler",
        ...     logger=orchestrator.logger,
        ...     poll_timeout=1.0
        ... )
        >>> handler.start()
        >>> # ... do work ...
        >>> handler.stop(timeout=2.0)
    """

    def __init__(
        self,
        channel: MessageChannel,
        message_handler: Callable[[ServiceMessage], None],
        name: str = "ChannelHandler",
        logger=None,
        poll_timeout: float = 1.0,
    ):
        """
        Initialize the channel handler.

        Args:
            channel (MessageChannel): MessageChannel instance to monitor.
            message_handler (Callable): Callback function to process received messages.
                                       Must accept a ServiceMessage as argument.
            name (str): Thread name for identification. Defaults to "ChannelHandler".
            logger: Logger instance for logging (optional). Should have debug, trace,
                   warning, and error methods.
            poll_timeout (float): Timeout for channel polling in seconds. Defaults to 1.0.
                                 Lower values provide faster shutdown response but higher CPU usage.
        """
        self.channel = channel
        self.message_handler = message_handler
        self.name = name
        self.logger = logger
        self.poll_timeout = poll_timeout

        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """
        Start the message handling thread.

        Creates and starts a daemon thread that continuously polls the message channel
        and invokes the message handler callback for each received message.

        Notes:
            - If the handler is already running, this method logs a warning and returns.
            - The thread is created as a daemon to allow graceful application shutdown.
            - Uses the configured name for easy identification in thread dumps.
        """
        if self._running:
            if self.logger:
                self.logger.warning(f"{self.name} already running")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True, name=self.name
        )
        self._thread.start()

        if self.logger:
            self.logger.debug(f"{self.name} started successfully")

    def stop(self, timeout: float = 2.0) -> None:
        """
        Stop the message handling thread.

        Signals the thread to stop and waits for it to terminate gracefully.
        If the thread doesn't stop within the timeout period, a warning is logged.

        Args:
            timeout (float): Maximum time in seconds to wait for thread termination.
                           Defaults to 2.0 seconds.

        Notes:
            - This method is idempotent - calling it multiple times is safe.
            - The thread will complete processing the current message before stopping.
            - If the thread is stuck, it will be left as a daemon and eventually
              terminated when the application exits.
        """
        if not self._running:
            return

        self._running = False

        if self._thread:
            self._thread.join(timeout=timeout)

            if self._thread.is_alive():
                if self.logger:
                    self.logger.warning(f"{self.name} did not stop properly")
            else:
                if self.logger:
                    self.logger.trace(f"{self.name} stopped successfully")

            self._thread = None

    def is_running(self) -> bool:
        """
        Check if the handler is currently running.

        Returns:
            bool: True if the handler thread is active, False otherwise.
        """
        return self._running

    def _run_loop(self) -> None:
        """
        Internal thread loop for processing messages.

        This method runs in a separate daemon thread and continuously polls
        the message channel for incoming messages. When a message is received,
        it invokes the configured message handler callback.

        The loop continues until the _running flag is set to False by the stop() method.

        Notes:
            - All exceptions in message handling are caught and logged to prevent
              thread termination.
            - Uses the configured poll_timeout to balance responsiveness and CPU usage.
        """
        while self._running:
            try:
                msg = self.channel.receive(timeout=self.poll_timeout)
                if msg:
                    self.message_handler(msg)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in {self.name}: {e}")
