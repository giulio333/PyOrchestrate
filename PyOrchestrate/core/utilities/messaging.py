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
CHUNK_SIZE = 8192  # Read in 8KB chunks
MAX_MESSAGE_SIZE = 100 * 1024 * 1024  # 100MB maximum message size
PROTOCOL_VERSION = "1.0"


def now_iso() -> str:
    """Return current timestamp in ISO format."""
    return datetime.now().isoformat()


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


@dataclass
class ServiceMessage:
    sender: str
    type: Literal["COMMAND", "STATUS"]
    payload: Dict[str, Any]  # Always a dict for consistency
    timestamp: datetime

    def to_dict(self) -> Dict[str, object]:
        timestamp = (
            self.timestamp.isoformat()
            if isinstance(self.timestamp, datetime)
            else self.timestamp
        )
        return {
            "sender": self.sender,
            "event_name": self.type,
            "payload": self.payload,
            "timestamp": timestamp,
        }

    def to_json(self, **json_kwargs) -> str:
        """Return a JSON string representation of the event.

        Passes json_kwargs to json.dumps (e.g. indent=2, ensure_ascii=False).
        """
        return json.dumps(
            self.to_dict(),
            **json_kwargs,
        )

    def to_bytes(self) -> bytes:
        """Convert ServiceMessage to bytes for transmission.

        Returns:
            Encoded message bytes with newline terminator
        """
        envelope = {
            "sender": self.sender,
            "event_name": self.type,
            "payload": self.payload,
            "timestamp": (
                self.timestamp.isoformat()
                if isinstance(self.timestamp, datetime)
                else self.timestamp
            ),
        }
        return (json.dumps(envelope, ensure_ascii=False) + "\n").encode()

    @classmethod
    def from_bytes(cls, raw_bytes: bytes) -> "ServiceMessage":
        """Create ServiceMessage from bytes received from transmission.

        Args:
            raw_bytes: Raw message bytes

        Returns:
            ServiceMessage instance

        Raises:
            json.JSONDecodeError: If the bytes cannot be decoded as JSON
            KeyError: If required fields are missing from the envelope
            ValueError: If timestamp cannot be parsed
        """
        envelope = json.loads(raw_bytes.decode().strip())

        # Parse timestamp back to datetime if it's a string
        timestamp = envelope["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            sender=envelope["sender"],
            type=envelope["event_name"],
            payload=envelope["payload"],
            timestamp=timestamp,
        )

    @classmethod
    def create_command(
        cls,
        sender: str,
        command: str,
        args: Optional[list] = None,
        request_id: Optional[str] = None,
        meta: Optional[dict] = None,
    ) -> "ServiceMessage":
        """Create a COMMAND type ServiceMessage.

        Args:
            sender: Message sender identifier
            command: Command name
            args: Optional command arguments
            request_id: Optional request identifier
            meta: Optional metadata

        Returns:
            ServiceMessage instance with type="COMMAND"
        """
        return cls(
            sender=sender,
            type="COMMAND",
            payload={
                "command": command,
                "args": args or [],
                "request_id": request_id or generate_request_id(),
                "timestamp": now_iso(),
                "meta": meta or {},
            },
            timestamp=datetime.now(),
        )

    @classmethod
    def create_command_response(
        cls,
        sender: str,
        status: Literal["success", "error"],
        code: int = 0,
        data: Optional[dict] = None,
        request_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> "ServiceMessage":
        """Create a COMMAND type ServiceMessage.

        Args:
            sender: Message sender identifier
            status: Command status (e.g., "success", "error")
            code: Command response code (e.g., 200, 404)
            data: Optional command data
            request_id: Optional request identifier
            error: Optional error information

        Returns:
            ServiceMessage instance with type="COMMAND"
        """
        return cls(
            sender=sender,
            type="COMMAND",
            payload={
                "status": status,
                "error": error,
                "code": code,
                "data": data or {},
                "request_id": request_id,
                "timestamp": now_iso(),
                "protocol_version": PROTOCOL_VERSION,
            },
            timestamp=datetime.now(),
        )

    @classmethod
    def create_status(
        cls,
        sender: str,
        status: str,
        event_name: Optional[str] = None,
        error: Optional[str] = None,
    ) -> "ServiceMessage":
        """Create a STATUS type ServiceMessage.

        Args:
            sender: Message sender identifier
            status: Status message content
            data: Optional additional data to include in the status message

        Returns:
            ServiceMessage instance with type="STATUS"
        """
        return cls(
            sender=sender,
            type="STATUS",
            payload={
                "status": status,
                "error": error or "",
                "event": event_name or "",
            },
            timestamp=datetime.now(),
        )

    def __str__(self) -> str:
        return f"ServiceMessage(sender={self.sender}, type={self.type})"


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

    def receive(self, timeout: float) -> Optional[ServiceMessage]:
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
        msg = None
        if self.a_type in ["thread", "process"]:
            try:
                msg = self._queue.get(timeout=timeout)  # Get only the message
            except queue.Empty:
                return None
        elif self.a_type == "unix_socket":
            msg = self._receive_from_unix_socket_server(timeout)
        elif self.a_type == "unix_socket_client":
            msg = self._receive_from_unix_socket_client(timeout)

        return msg

    def send_and_receive(
        self, msg: ServiceMessage, timeout: float = 5.0, auto_close: bool = False
    ) -> Optional[ServiceMessage]:
        """Send a message and wait for response (client mode only).

        Args:
            msg: ServiceMessage to send.
            timeout: Maximum time to wait for response in seconds.
            auto_close: Whether to close the connection automatically after receiving a response.

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

        if auto_close:
            self.close()

        return response

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
        msg_data = msg.to_bytes()

        # Use slice copy to avoid modification during iteration
        for client in self._clients[:]:
            try:
                # Use sendall() to ensure complete message delivery
                client.sendall(msg_data)
            except BlockingIOError:
                # Buffer is full but client is still connected - skip for now
                # The message will be lost but the client remains connected
                print(f"Warning: Send buffer full for client, message dropped")
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                # Remove disconnected clients
                print(f"Removing disconnected client: {e}")
                self._clients.remove(client)
                client.close()

    def _send_to_unix_socket_client(self, msg: ServiceMessage) -> bool:
        """Send message to server (client mode). Returns True if successful."""
        if not self._socket:
            if not self._connect_to_server():
                return False

        try:
            assert self._socket is not None, "Socket must be connected before sending"
            envelope = msg.to_bytes()
            # Use sendall() to ensure complete message delivery
            self._socket.sendall(envelope)
            return True
        except BlockingIOError:
            # Buffer is full but connection is still alive
            print("Warning: Send buffer full, message dropped")
            return False
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

    def _receive_complete_message(
        self, sock: socket.socket, timeout: float
    ) -> Optional[bytes]:
        """Receive a complete message from socket, reading until newline delimiter.

        Args:
            sock: Socket to read from
            timeout: Timeout in seconds

        Returns:
            Complete message bytes or None if timeout/error
        """
        sock.settimeout(timeout)
        buffer = b""

        try:
            while True:
                chunk = sock.recv(CHUNK_SIZE)
                if not chunk:
                    return None  # Connection closed

                buffer += chunk

                # Check if we have a complete message (ends with newline)
                if b"\n" in buffer:
                    # Return only the first complete message
                    message, remainder = buffer.split(b"\n", 1)
                    # Store remainder for next read if needed (currently not implemented)
                    return message + b"\n"

                # Safety check: prevent unbounded memory growth
                if len(buffer) > MAX_MESSAGE_SIZE:
                    raise ValueError(
                        f"Message exceeds maximum size of {MAX_MESSAGE_SIZE} bytes"
                    )

        except socket.timeout:
            return None
        except (BrokenPipeError, ConnectionResetError, OSError):
            return None

    def _receive_from_unix_socket_server(self, timeout) -> Optional[ServiceMessage]:
        """Receive message from UNIX socket clients (server mode).

        Uses select() to efficiently handle both new connections and existing client messages.

        Args:
            timeout: Maximum time in seconds to wait for a message.
        """
        import select

        try:
            assert self._socket is not None, "Socket must be connected before accepting"

            # Use select to wait for either new connections or client data
            # Build list of sockets to monitor: server socket + all client sockets
            readable_sockets = [self._socket] + self._clients

            # Wait for any socket to become readable (with timeout)
            ready_to_read, _, _ = select.select(readable_sockets, [], [], timeout)

            if not ready_to_read:
                return None  # Timeout, no activity

            # Check if server socket is ready (new connection)
            if self._socket in ready_to_read:
                try:
                    client_socket, _ = self._socket.accept()
                    client_socket.setblocking(
                        False
                    )  # Set non-blocking for future reads
                    self._clients.append(client_socket)
                except (socket.timeout, BlockingIOError):
                    pass  # Should not happen with select, but handle anyway

            # Check for messages from existing clients
            for client in self._clients[:]:
                if client in ready_to_read:
                    try:
                        # Use a minimal timeout since select() already confirmed data is ready
                        data = self._receive_complete_message(client, timeout=0.1)
                        if data:
                            return ServiceMessage.from_bytes(data)
                        else:
                            # Connection closed gracefully
                            self._clients.remove(client)
                            client.close()
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        # Log error but continue with other clients
                        pass
                    except (BrokenPipeError, ConnectionResetError, OSError):
                        # Remove disconnected clients
                        self._clients.remove(client)
                        client.close()

            return None
        except Exception:
            return None

    def _receive_from_unix_socket_client(
        self, timeout: float = 5.0
    ) -> Optional[ServiceMessage]:
        """Receive a message from server (client mode)."""
        if not self._socket:
            return None

        try:
            data = self._receive_complete_message(self._socket, timeout)
            if data:
                return ServiceMessage.from_bytes(data)
        except (json.JSONDecodeError, KeyError, ValueError, OSError):
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
