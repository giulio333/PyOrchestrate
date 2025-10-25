"""
Command Interface for Orchestrator.

This module provides the CommandInterface class that manages external command
processing for the orchestrator. It encapsulates ZeroMQ command channel setup,
command handler integration, and message processing logic.
"""

from typing import Optional, TYPE_CHECKING

from PyOrchestrate.core.utilities.messaging import MessageChannel, ServiceMessage
from PyOrchestrate.core.utilities.command_handler import CommandHandler
from PyOrchestrate.core.orchestrator.channel_handler import ChannelHandler
from PyOrchestrate.core.orchestrator.event_store import EventStore

if TYPE_CHECKING:
    from loguru import Logger


class CommandInterface:
    """
    Manages external command interface for orchestrator.

    The CommandInterface encapsulates all logic for handling external commands
    from CLI clients. It manages:
    - ZeroMQ ROUTER socket for command communication
    - CommandHandler for executing commands
    - ChannelHandler for async message processing
    - Event tracking for command execution

    This class provides clean lifecycle management with start/stop methods
    and automatic error handling with event store integration.

    Example:
        ```python
        cmd_interface = CommandInterface(
            orchestrator=orchestrator,
            zmq_address="tcp://*:5555",
            allowed_commands={"ps", "shutdown"},
            event_store=event_store,
            logger=logger
        )

        # Start command interface
        cmd_interface.start()

        # Later, during shutdown
        cmd_interface.stop()
        ```

    Thread Safety:
        This class is thread-safe. The ChannelHandler runs in a separate thread
        and handles command messages asynchronously.
    """

    def __init__(
        self,
        orchestrator,
        zmq_address: str,
        allowed_commands: set[str] | str | None,
        event_store: EventStore,
        logger: "Logger",
    ):
        """
        Initialize the command interface.

        Args:
            orchestrator: Orchestrator instance (for command execution)
            zmq_address: ZeroMQ address for command channel (e.g., "tcp://*:5555")
            allowed_commands: Set of allowed commands, preset name, or None for all
            event_store: EventStore for tracking command execution
            logger: Logger instance for logging
        """
        self.orchestrator = orchestrator
        self.zmq_address = zmq_address
        self.event_store = event_store
        self.logger = logger

        # Create command channel (ZeroMQ ROUTER socket)
        self.command_channel = MessageChannel("zmq_router", zmq_address)

        # Create command handler
        self.command_handler = CommandHandler(orchestrator, allowed_commands)

        # Channel handler (will be started later)
        self._channel_handler: Optional[ChannelHandler] = None

        self.logger.debug(f"Command interface initialized on ZMQ: {zmq_address}")

    def start(self) -> None:
        """
        Start the command interface.

        Creates and starts a ChannelHandler thread to process incoming
        command messages asynchronously. The handler will continuously
        poll the command channel and invoke handle_command for each message.

        This method should be called during orchestrator initialization.

        Raises:
            RuntimeError: If command interface is already started
        """
        if self._channel_handler is not None:
            raise RuntimeError("Command interface is already started")

        self._channel_handler = ChannelHandler(
            channel=self.command_channel,
            message_handler=self.handle_command,
            name="OrchestratorCommandHandler",
            logger=self.logger,
            poll_timeout=1.0,
        )
        self._channel_handler.start()
        self.logger.debug("Command interface started successfully")

    def stop(self, timeout: float = 2.0) -> None:
        """
        Stop the command interface gracefully.

        Stops the channel handler thread and closes the command channel.
        This method blocks until the handler thread terminates or timeout expires.

        Args:
            timeout: Maximum time to wait for handler thread to stop (seconds)
        """
        if self._channel_handler:
            self._channel_handler.stop(timeout=timeout)
            self._channel_handler = None

        if self.command_channel:
            self.command_channel.close()

        self.logger.debug("Command interface stopped")

    def handle_command(self, request_msg: ServiceMessage) -> None:
        """
        Process external command from CLI client.

        This method is invoked by ChannelHandler for each incoming command message.
        It validates the request, executes the command via CommandHandler, tracks
        errors to event store, and sends response back to the client.

        Args:
            request_msg: ServiceMessage containing command request

        Error Handling:
            - Validation errors are tracked to event store and returned as error responses
            - Command execution errors are caught, logged, tracked, and returned as error responses
            - All errors result in structured ServiceMessage error responses sent back to client
        """
        request_id = None

        try:
            cmd_data = request_msg.payload  # Already a dict
            command = cmd_data.get("command")
            request_id = cmd_data.get("request_id")

            # Validate command presence
            if not command:
                raise ValueError("Command is required")

            try:
                # Execute command via CommandHandler
                response_msg = self.command_handler.execute_command_msg(request_msg)
            except Exception as e:
                # Convert command execution errors to structured error responses
                self.logger.warning(f"Command handling failed: {e}")

                # Track error in event store
                self.event_store.record(
                    category="cli",
                    event_name="CLI_ERROR",
                    severity="ERROR",
                    data={"error": str(e)},
                )

                # Create structured error response
                response_msg = ServiceMessage.create_command_response(
                    sender="orchestrator",
                    status="error",
                    error=str(e),
                    request_id=request_id,
                )

            # Send response back through command channel
            assert self.command_channel, "Command channel not initialized"
            self.command_channel.send("cli", response_msg)

        except Exception as e:
            # Outer exception handler for validation and unexpected errors
            self.logger.error(f"Error processing external command: {e}")

            # Track error
            self.event_store.record(
                category="cli",
                event_name="CLI_ERROR",
                severity="ERROR",
                data={"error": str(e)},
            )

            # Send error response if channel is available
            if self.command_channel:
                self.command_channel.send(
                    "cli",
                    ServiceMessage.create_command_response(
                        sender="orchestrator",
                        status="error",
                        error=str(e),
                        request_id=request_id,
                    ),
                )

    def is_running(self) -> bool:
        """
        Check if command interface is currently running.

        Returns:
            bool: True if channel handler is running, False otherwise
        """
        return self._channel_handler is not None and self._channel_handler.is_running()
