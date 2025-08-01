import queue
import multiprocessing
import socket
import os
import json
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Union, Optional, Literal


# Constants
DEFAULT_SOCKET_PATH = "/tmp/pyorchestrate.sock"
SOCKET_LISTEN_BACKLOG = 5
SOCKET_TIMEOUT = 1.0
CLIENT_RECEIVE_TIMEOUT = 0.1
BUFFER_SIZE = 4096


@dataclass
class ServiceMessage:
    sender: str
    type: Literal["COMMAND", "STATUS"]
    payload: str
    timestamp: datetime


class MessageChannel:
    """A message channel for communication between agents and orchestrators.

    Provides a unified interface for sending and receiving messages across different
    communication protocols including thread queues, process queues, and UNIX domain sockets.
    The channel automatically handles the underlying communication mechanism based on the
    specified type, allowing seamless communication between system components.

    Attributes:
        a_type: The type of communication channel ('thread', 'process', or 'unix_socket').
        socket_path: Path to the UNIX domain socket file (only used for 'unix_socket' type).

    Example:
        >>> channel = MessageChannel('thread')
        >>> msg = ServiceMessage('agent1', 'STATUS', 'running', datetime.now())
        >>> channel.send('target', msg)
        >>> received = channel.receive(timeout=1.0)
    """

    def __init__(
        self,
        a_type: Literal["thread", "process", "unix_socket"],
        socket_path: str = DEFAULT_SOCKET_PATH,
    ):
        self.a_type = a_type
        self.socket_path = socket_path

        if a_type == "thread":
            self._queue = queue.Queue()
        elif a_type == "process":
            self._queue = multiprocessing.Queue()
        elif a_type == "unix_socket":
            self._setup_unix_socket()
        else:
            raise ValueError(
                "Invalid a_type. Must be 'thread', 'process', or 'unix_socket'."
            )

    def send(self, target: str, msg: ServiceMessage) -> None:
        """Send a message through the communication channel.

        Sends a ServiceMessage through the appropriate communication mechanism based on
        the channel type. For thread/process queues, the message is queued directly.
        For UNIX sockets, the message is broadcast to all connected clients.

        Args:
            target: The intended recipient identifier (currently unused but kept for
                   compatibility and potential future routing features).
            msg: The ServiceMessage instance to send containing sender, type, payload,
                and timestamp information.

        Note:
            The target parameter is currently ignored in the implementation but maintained
            for API compatibility and potential future message routing functionality.
        """
        if self.a_type in ["thread", "process"]:
            self._queue.put(msg)  # Store only the message
        elif self.a_type == "unix_socket":
            self._send_to_unix_socket(msg)

    def receive(self, timeout: Optional[float] = None) -> Optional[ServiceMessage]:
        """Receive a message from the communication channel.

        Attempts to receive a ServiceMessage from the appropriate communication mechanism.
        For thread/process queues, it retrieves from the queue with optional timeout.
        For UNIX sockets, it checks for new connections and reads from existing clients.

        Args:
            timeout: Maximum time in seconds to wait for a message. If None, the method
                    will block indefinitely for thread/process queues, or use the default
                    CLIENT_RECEIVE_TIMEOUT for UNIX sockets.

        Returns:
            A ServiceMessage if one was received, None if no message is available or
            timeout was reached.

        Note:
            The timeout parameter controls the maximum wait time for all channel types.
        """
        if self.a_type in ["thread", "process"]:
            try:
                msg = self._queue.get(timeout=timeout)  # Get only the message
            except queue.Empty:
                return None
        elif self.a_type == "unix_socket":
            msg = self._receive_from_unix_socket(timeout)

        return msg

    def close(self):
        """Close the message channel and cleanup resources.

        Performs cleanup operations specific to the communication channel type.
        For UNIX socket channels, this includes:
        - Closing all active client connections
        - Shutting down the server socket
        - Removing the socket file from the filesystem

        For thread and process queues, no cleanup is necessary as the queue
        objects are automatically garbage collected.

        Note:
            It's important to call this method when done with UNIX socket channels
            to prevent resource leaks and ensure the socket file is properly removed.
        """
        if self.a_type == "unix_socket":
            # Close all client connections
            for client in self._clients:
                client.close()
            self._clients.clear()

            # Close server socket
            self._socket.close()

            # Remove socket file
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)

    def _send_to_unix_socket(self, msg: ServiceMessage) -> None:
        """Send message to all connected UNIX socket clients."""
        msg_data = (
            json.dumps(
                {
                    "sender": msg.sender,
                    "type": msg.type,
                    "payload": msg.payload,
                    "timestamp": msg.timestamp.isoformat(),
                }
            ).encode()
            + b"\n"
        )

        # Use slice copy to avoid modification during iteration
        for client in self._clients[:]:
            try:
                client.send(msg_data)
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                # Remove disconnected clients
                self._clients.remove(client)
                client.close()

    def _receive_from_unix_socket(
        self, timeout: Optional[float] = None
    ) -> Optional[ServiceMessage]:
        """Receive message from UNIX socket clients.

        Args:
            timeout: Maximum time in seconds to wait for a message. If None, uses
                    the default CLIENT_RECEIVE_TIMEOUT.
        """
        # Use provided timeout or default
        client_timeout = timeout if timeout is not None else CLIENT_RECEIVE_TIMEOUT

        try:
            # Accept new connections
            try:
                client_socket, _ = self._socket.accept()
                self._clients.append(client_socket)
            except socket.timeout:
                pass  # No new connections

            # Check for messages from existing clients
            for client in self._clients[:]:
                try:
                    client.settimeout(client_timeout)
                    data = client.recv(BUFFER_SIZE)
                    if data:
                        msg_str = data.decode().strip()
                        msg_data = json.loads(msg_str)
                        return ServiceMessage(
                            sender=msg_data["sender"],
                            type=msg_data["type"],
                            payload=msg_data["payload"],
                            timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                        )
                except (socket.timeout, json.JSONDecodeError, KeyError):
                    pass  # No data or invalid data
                except (BrokenPipeError, ConnectionResetError, OSError):
                    # Remove disconnected clients
                    self._clients.remove(client)
                    client.close()

            return None
        except Exception:
            return None

    def _setup_unix_socket(self):
        """
        Setup UNIX domain socket for external communication.

        Creates a UNIX domain socket, binds it to the specified path,
        and configures it to listen for incoming connections with a timeout.
        """
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Remove socket file if it exists
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

        # Bind and listen
        self._socket.bind(self.socket_path)
        self._socket.listen(SOCKET_LISTEN_BACKLOG)
        self._socket.settimeout(SOCKET_TIMEOUT)  # Non-blocking with timeout

        self._clients: list[socket.socket] = []  # Store client connections
