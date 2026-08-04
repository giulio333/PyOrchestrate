"""
Channel Handler Module

This module provides the ChannelHandler class for managing message channel
communication in separate threads, encapsulating thread lifecycle management.
"""

import atexit
import sys
import threading
import weakref
from typing import Callable, Optional

import zmq

from PyOrchestrate.core.utilities.messaging import MessageChannel, ServiceMessage

# Time each orphaned handler is given to leave its loop during the atexit
# backstop. Handlers are signalled first and joined afterwards, so the waits
# overlap instead of adding up.
_ATEXIT_JOIN_TIMEOUT = 2.0

# ZeroMQ errors that mean the socket or its context is gone for good, as
# opposed to a poll that happened to fail.
_TERMINAL_ZMQ_ERRNOS = frozenset({zmq.ENOTSOCK, zmq.ETERM})

_live_handlers: "weakref.WeakSet[ChannelHandler]" = weakref.WeakSet()
_live_handlers_lock = threading.Lock()


def _channel_is_gone(error: BaseException) -> bool:
    """
    Tell a dead channel from a failed poll.

    A closed queue raises ``OSError`` ("handle is closed") or ``ValueError``,
    an exhausted pipe raises ``EOFError``, and a closed ZeroMQ socket or a
    terminated context raises ``zmq.ZMQError`` with ``ENOTSOCK`` or ``ETERM``.
    None of them can be recovered from by polling again.

    Args:
        error (BaseException): Exception raised by ``MessageChannel.receive()``.

    Returns:
        bool: True if the channel can no longer produce messages.
    """
    if isinstance(error, (OSError, ValueError, EOFError)):
        return True
    return isinstance(error, zmq.ZMQError) and error.errno in _TERMINAL_ZMQ_ERRNOS


def _stop_live_handlers() -> None:
    """
    Stop every handler still running when the interpreter starts exiting.

    Registered with :mod:`atexit`, which runs before the runtime begins
    finalizing: a handler nobody stopped leaves its loop here, while joining
    and logging are still safe.
    """
    with _live_handlers_lock:
        handlers = list(_live_handlers)

    for handler in handlers:
        handler._signal_stop()
    for handler in handlers:
        handler.stop(timeout=_ATEXIT_JOIN_TIMEOUT)


atexit.register(_stop_live_handlers)


class ChannelHandler:
    """
    Handles message channel communication in a separate thread.

    Encapsulates thread lifecycle management for message processing,
    providing a clean interface for starting, stopping, and handling
    messages from a MessageChannel.

    This class follows the Single Responsibility Principle by managing
    only the thread lifecycle and message polling, delegating message
    processing to a provided callback function.

    The polling thread is a daemon, so it never keeps the interpreter alive.
    Two guarantees keep it from aborting the process on the way out: a channel
    closed underneath the loop ends the loop instead of being logged once per
    poll, and an :mod:`atexit` hook signals and joins any handler still running
    when the interpreter starts exiting.

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
            - The handler is registered for the atexit backstop, which stops it
              even if nobody calls :meth:`stop`.
        """
        if self._running:
            self._log("warning", f"{self.name} already running")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True, name=self.name
        )
        with _live_handlers_lock:
            _live_handlers.add(self)
        self._thread.start()

        self._log("debug", f"{self.name} started successfully")

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
            - A thread that already left its loop on its own, because the channel
              was closed, is still joined and cleared here.
        """
        if not self._running and self._thread is None:
            return

        self._signal_stop()

        if self._thread:
            self._thread.join(timeout=timeout)

            if self._thread.is_alive():
                self._log("warning", f"{self.name} did not stop properly")
            else:
                self._log("trace", f"{self.name} stopped successfully")

            self._thread = None

    def _signal_stop(self) -> None:
        """
        Ask the loop to leave without waiting for it.

        Separate from :meth:`stop` so several handlers can be signalled first
        and joined afterwards, which is what the atexit backstop does.
        """
        self._running = False
        with _live_handlers_lock:
            _live_handlers.discard(self)

    def is_running(self) -> bool:
        """
        Check if the handler is currently running.

        Returns:
            bool: True if the handler thread is active, False otherwise.
        """
        return self._running

    def _log(self, level: str, message: str) -> None:
        """
        Log a message unless the interpreter is finalizing.

        The loop runs in a daemon thread that can outlive the code that started
        it. Writing to ``stderr`` while the runtime tears down its buffers
        aborts the process with ``_enter_buffered_busy``, so during finalization
        the message is dropped instead.

        Args:
            level (str): Name of the logger method to call ("debug", "error", ...).
            message (str): Message to log.
        """
        if self.logger is None or sys.is_finalizing():
            return
        getattr(self.logger, level)(message)

    def _run_loop(self) -> None:
        """
        Internal thread loop for processing messages.

        This method runs in a separate daemon thread and continuously polls
        the message channel for incoming messages. When a message is received,
        it invokes the configured message handler callback.

        The loop continues until the _running flag is set to False by the stop()
        method, or until the channel is closed underneath it.

        Notes:
            - A closed channel ends the loop instead of being logged: retrying
              would only produce the same error, once per poll.
            - Every other exception, from the poll or from the message handler,
              is caught and logged so that the thread survives it.
            - Uses the configured poll_timeout to balance responsiveness and CPU usage.
        """
        while self._running:
            try:
                msg = self.channel.receive(timeout=self.poll_timeout)
            except Exception as e:
                if _channel_is_gone(e):
                    self._signal_stop()
                    self._log("debug", f"{self.name} stopping: channel closed ({e})")
                    return
                self._log("error", f"Error in {self.name}: {e}")
                continue

            if not msg:
                continue

            try:
                self.message_handler(msg)
            except Exception as e:
                self._log("error", f"Error in {self.name}: {e}")
