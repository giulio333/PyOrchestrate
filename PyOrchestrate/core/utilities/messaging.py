import queue
import multiprocessing
import socket
import os
import json
import time
import uuid
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Union, Optional, Literal, Dict, Any


# Constants
DEFAULT_SOCKET_PATH = "/tmp/pyorchestrate.sock"
SOCKET_LISTEN_BACKLOG = 5
SOCKET_TIMEOUT = 1.0
CLIENT_RECEIVE_TIMEOUT = 0.1
BUFFER_SIZE = 4096
PROTOCOL_VERSION = "1.0"


def now_iso() -> str:
    """Return current timestamp in ISO format."""
    return datetime.now().isoformat()


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def make_request(
    command: str,
    args: Optional[list] = None,
    request_id: Optional[str] = None,
    meta: Optional[dict] = None,
) -> dict:
    """Create a standardized request payload.

    Args:
        command: Command name
        args: Command arguments
        request_id: Optional request ID for correlation
        meta: Optional metadata

    Returns:
        Standardized request dict
    """
    return {
        "command": command,
        "args": args or [],
        "request_id": request_id or generate_request_id(),
        "timestamp": now_iso(),
        "meta": meta or {},
    }


def make_response(
    status: str,
    data: Any = None,
    message: Optional[str] = None,
    code: int = 0,
    request_id: Optional[str] = None,
    error: Optional[dict] = None,
) -> dict:
    """Create a standardized response payload.

    Args:
        status: "success" or "error"
        data: Response data
        message: Human readable message
        code: Error code (0 = success)
        request_id: Request ID for correlation
        error: Error details dict

    Returns:
        Standardized response dict
    """
    response = {
        "status": status,
        "code": code,
        "message": message or "",
        "data": data or {},
        "request_id": request_id,
        "timestamp": now_iso(),
        "protocol_version": PROTOCOL_VERSION,
    }

    if status == "error" and error:
        response["error"] = error
    elif status == "error" and isinstance(data, Exception):
        response["error"] = {"type": type(data).__name__, "message": str(data)}
        response["data"] = {}

    return response


def pack_envelope(sender: str, msg_type: str, payload: dict) -> bytes:
    """Pack a message envelope for transmission.

    Args:
        sender: Message sender identifier
        msg_type: Message type ("COMMAND", "STATUS", etc.)
        payload: Message payload dict

    Returns:
        Encoded message bytes with newline terminator
    """
    envelope = {
        "sender": sender,
        "type": msg_type,
        "payload": payload,
        "timestamp": now_iso(),
    }
    return (json.dumps(envelope, ensure_ascii=False) + "\n").encode()


def unpack_envelope(raw_bytes: bytes) -> dict:
    """Unpack a message envelope from transmission.

    Args:
        raw_bytes: Raw message bytes

    Returns:
        Unpacked envelope dict
    """
    return json.loads(raw_bytes.decode().strip())


@dataclass
class ServiceMessage:
    sender: str
    type: Literal["COMMAND", "STATUS"]
    payload: Dict[str, Any]  # Always a dict for consistency
    timestamp: datetime


class MessageChannel:
    """A message channel for communication between agents and orchestrators.

    Provides a unified interface for sending and receiving messages across different
    communication protocols including thread queues, process queues, and UNIX domain sockets.
    The channel automatically handles the underlying communication mechanism based on the
    specified type, allowing seamless communication between system components.

    Attributes:
        a_type: The type of communication channel ('thread', 'process', 'unix_socket', or 'unix_socket_client').
        socket_path: Path to the UNIX domain socket file (only used for 'unix_socket' types).

    Example:
        >>> # Server mode
        >>> server = MessageChannel('unix_socket')
        >>> msg = ServiceMessage('agent1', 'STATUS', 'running', datetime.now())
        >>> server.send('target', msg)
        >>> received = server.receive(timeout=1.0)

        >>> # Client mode
        >>> client = MessageChannel('unix_socket_client', '/tmp/pyorchestrate.sock')
        >>> response = client.send_and_receive(msg, timeout=5.0)
        >>> client.close()
    """

    def __init__(
        self,
        a_type: Literal["thread", "process", "unix_socket", "unix_socket_client"],
        socket_path: str = DEFAULT_SOCKET_PATH,
    ):
        self.a_type = a_type
        self.socket_path = socket_path

        if a_type == "thread":
            self._queue = queue.Queue()
        elif a_type == "process":
            self._queue = multiprocessing.Queue()
        elif a_type == "unix_socket":
            self._setup_unix_socket_server()
            self._clients: list[socket.socket] = []  # Store client connections
        elif a_type == "unix_socket_client":
            self._socket: Optional[socket.socket] = None
        else:
            raise ValueError(
                "Invalid a_type. Must be 'thread', 'process', 'unix_socket', or 'unix_socket_client'."
            )

    def send(self, target: str, msg: ServiceMessage) -> None:
        """Send a message through the communication channel.

        Sends a ServiceMessage through the appropriate communication mechanism based on
        the channel type. For thread/process queues, the message is queued directly.
        For UNIX sockets, the message is broadcast to all connected clients (server mode)
        or sent to the server (client mode).

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
            self._send_to_unix_socket_server(msg)
        elif self.a_type == "unix_socket_client":
            self._send_to_unix_socket_client(msg)

    def receive(self, timeout: Optional[float] = None) -> Optional[ServiceMessage]:
        """Receive a message from the communication channel.

        Attempts to receive a ServiceMessage from the appropriate communication mechanism.
        For thread/process queues, it retrieves from the queue with optional timeout.
        For UNIX sockets, it checks for new connections and reads from existing clients
        (server mode) or reads from the server connection (client mode).

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
            msg = self._receive_from_unix_socket_server(timeout)
        elif self.a_type == "unix_socket_client":
            msg = self._receive_from_unix_socket_client(
                timeout or CLIENT_RECEIVE_TIMEOUT
            )

        return msg

    def close(self):
        """Close the message channel and cleanup resources.

        Performs cleanup operations specific to the communication channel type.
        For UNIX socket channels, this includes:
        - Closing all active client connections (server mode)
        - Closing the client connection (client mode)
        - Shutting down the server socket (server mode)
        - Removing the socket file from the filesystem (server mode)

        For thread and process queues, no cleanup is necessary as the queue
        objects are automatically garbage collected.

        Note:
            It's important to call this method when done with UNIX socket channels
            to prevent resource leaks and ensure the socket file is properly removed.
        """
        if self.a_type == "unix_socket":
            # Close all client connections
            if hasattr(self, "_clients"):
                for client in self._clients:
                    client.close()
                self._clients.clear()

            # Close server socket
            if hasattr(self, "_socket") and self._socket:
                self._socket.close()

            # Remove socket file
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
        elif self.a_type == "unix_socket_client":
            if hasattr(self, "_socket") and self._socket:
                self._socket.close()
                self._socket = None

    def _send_to_unix_socket_server(self, msg: ServiceMessage) -> None:
        """Send message to all connected UNIX socket clients (server mode)."""
        msg_data = pack_envelope(msg.sender, msg.type, msg.payload)

        # Use slice copy to avoid modification during iteration
        for client in self._clients[:]:
            try:
                client.send(msg_data)
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                # Remove disconnected clients
                self._clients.remove(client)
                client.close()

    def _send_to_unix_socket_client(self, msg: ServiceMessage) -> bool:
        """Send message to server (client mode). Returns True if successful."""
        if not self._socket:
            if not self._connect_to_server():
                return False

        try:
            assert self._socket is not None, "Socket must be connected before sending"
            envelope = pack_envelope(msg.sender, msg.type, msg.payload)
            self._socket.send(envelope)
            return True
        except (BrokenPipeError, ConnectionResetError, OSError):
            return False

    def _connect_to_server(self) -> bool:
        """Connect to server (client mode). Returns True if successful."""
        try:
            self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket.connect(self.socket_path)
            return True
        except (FileNotFoundError, ConnectionRefusedError, OSError):
            if self._socket:
                self._socket.close()
                self._socket = None
            return False

    def _receive_from_unix_socket_server(
        self, timeout: Optional[float] = None
    ) -> Optional[ServiceMessage]:
        """Receive message from UNIX socket clients (server mode).

        Args:
            timeout: Maximum time in seconds to wait for a message. If None, uses
                    the default CLIENT_RECEIVE_TIMEOUT.
        """
        # Use provided timeout or default
        client_timeout = timeout if timeout is not None else CLIENT_RECEIVE_TIMEOUT

        try:
            # Accept new connections
            try:
                assert (
                    self._socket is not None
                ), "Socket must be connected before accepting"
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
                        envelope = unpack_envelope(data)
                        if envelope:
                            return ServiceMessage(
                                sender=envelope["sender"],
                                type=envelope["type"],
                                payload=envelope["payload"],
                                timestamp=envelope["timestamp"],
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

    def send_and_receive(
        self, msg: ServiceMessage, timeout: float = 5.0
    ) -> Optional[ServiceMessage]:
        """Send a message and wait for response (client mode only).

        Args:
            msg: ServiceMessage to send.
            timeout: Maximum time to wait for response in seconds.

        Returns:
            ServiceMessage response if successful, None otherwise.
        """
        if self.a_type != "unix_socket_client":
            raise ValueError(
                "send_and_receive is only available for unix_socket_client mode"
            )

        if not self._socket:
            if not self._connect_to_server():
                return None

        if not self._send_to_unix_socket_client(msg):
            self.close()
            return None

        response = self._receive_from_unix_socket_client(timeout)
        self.close()
        return response

    def _receive_from_unix_socket_client(
        self, timeout: float = 5.0
    ) -> Optional[ServiceMessage]:
        """Receive a message from server (client mode)."""
        if not self._socket:
            return None

        try:
            self._socket.settimeout(timeout)
            data = self._socket.recv(BUFFER_SIZE)
            if data:
                envelope = unpack_envelope(data)
                if envelope:
                    return ServiceMessage(
                        sender=envelope["sender"],
                        type=envelope["type"],
                        payload=envelope["payload"],
                        timestamp=envelope["timestamp"],
                    )
        except (socket.timeout, json.JSONDecodeError, KeyError, OSError):
            pass
        return None

    def _setup_unix_socket_server(self):
        """
        Setup UNIX domain socket for external communication (server mode).

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
