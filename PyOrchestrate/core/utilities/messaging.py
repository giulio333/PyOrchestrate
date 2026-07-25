import queue
import multiprocessing
import json
import uuid
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Literal, Dict, Any
import zmq

# Constants
DEFAULT_ZMQ_ADDRESS = "tcp://127.0.0.1:5555"
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
        """Create a COMMAND type ServiceMessage representing a response.

        The payload follows a standard shape used by the CLI command interface:
        - status: "success" or "error"
        - code: numeric status/code (0 for generic success, or HTTP-like error codes)
        - data: dict with response data when status is "success"
        - error: human-readable error string when status is "error"
        - request_id: correlates this response to the original request
        - protocol_version: the protocol version used by the framework

        Args:
            sender: Message sender identifier (e.g. "orchestrator" or "command_handler").
            status: Command status ("success" or "error").
            code: Numeric response code (default 0).
            data: Optional payload data for successful responses.
            request_id: Optional request identifier to correlate request/response.
            error: Optional error information (string) for error responses.

        Returns:
            ServiceMessage instance with type="COMMAND" and a standardized payload.
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
    communication protocols including thread queues, process queues, and ZeroMQ sockets.
    The channel automatically handles the underlying communication mechanism based on the
    specified type, allowing seamless communication between system components.

    Attributes:
        a_type: The type of communication channel ('thread', 'process', 'zmq_router', or 'zmq_dealer').
        zmq_address: ZeroMQ address (only used for ZMQ types, e.g., 'tcp://127.0.0.1:5555').

    Example:
        >>> # Server mode (orchestrator)
        >>> server = MessageChannel('zmq_router', 'tcp://*:5555')
        >>> msg = ServiceMessage('agent1', 'STATUS', 'running', datetime.now())
        >>> server.send('target', msg)
        >>> received = server.receive(timeout=1.0)

        >>> # Client mode (CLI/web service)
        >>> client = MessageChannel('zmq_dealer', 'tcp://127.0.0.1:5555')
        >>> response = client.send_and_receive(msg, timeout=5.0)
        >>> client.close()
    """

    def __init__(
        self,
        a_type: Literal["thread", "process", "zmq_router", "zmq_dealer"],
        zmq_address: str = DEFAULT_ZMQ_ADDRESS,
    ):
        self.a_type = a_type
        self.zmq_address = zmq_address
        self._zmq_context: Optional[zmq.Context] = None
        self._zmq_socket: Optional[zmq.Socket] = None

        if a_type == "thread":
            self._queue = queue.Queue()
        elif a_type == "process":
            self._queue = multiprocessing.Queue()
        elif a_type == "zmq_router":
            self._setup_zmq_router()
        elif a_type == "zmq_dealer":
            self._setup_zmq_dealer()
        else:
            raise ValueError(
                "Invalid a_type. Must be 'thread', 'process', 'zmq_router', or 'zmq_dealer'."
            )

    def send(self, target: str, msg: ServiceMessage) -> None:
        """Send a message through the communication channel.

        Sends a ServiceMessage through the appropriate communication mechanism based on
        the channel type. For thread/process queues, the message is queued directly.
        For ZMQ sockets, the message is sent as JSON frames.

        Args:
            target: The intended recipient identifier. For ZMQ ROUTER, this is used
                   for routing. For queues, it's ignored.
            msg: The ServiceMessage instance to send containing sender, type, payload,
                and timestamp information.
        """
        if self.a_type in ["thread", "process"]:
            self._queue.put(msg)
        elif self.a_type in ["zmq_router", "zmq_dealer"]:
            self._send_zmq(target, msg)

    def receive(self, timeout: Optional[float]) -> Optional[ServiceMessage]:
        """Receive a message from the communication channel.

        Args:
            timeout: Maximum time in seconds to wait for a message. If None, the
                     call may block indefinitely for queue-based channels or use the
                     default blocking behaviour for ZMQ sockets.

        Returns:
            A ServiceMessage if one was received, None if no message is available or
            timeout was reached.
        """
        if self.a_type in ["thread", "process"]:
            try:
                msg = self._queue.get(timeout=timeout)
                return msg
            except queue.Empty:
                return None
        elif self.a_type in ["zmq_router", "zmq_dealer"]:
            return self._receive_zmq(timeout)

    def send_and_receive(
        self, msg: ServiceMessage, timeout: float = 5.0, auto_close: bool = False
    ) -> Optional[ServiceMessage]:
        """Send a message and wait for response (dealer mode only).

        Args:
            msg: ServiceMessage to send.
            timeout: Maximum time to wait for response in seconds.
            auto_close: Whether to close the connection after receiving response.

        Returns:
            ServiceMessage response if successful, None otherwise.
        """
        if self.a_type != "zmq_dealer":
            raise ValueError("send_and_receive is only available for zmq_dealer mode")

        self.send("", msg)  # Empty target for dealer
        response = self.receive(timeout)

        if auto_close:
            self.close()

        return response

    def close(self):
        """Close the message channel and cleanup resources.

        For ZMQ channels, closes the socket and terminates the context.
        For thread/process queues, no cleanup is necessary.
        """
        if self.a_type in ["zmq_router", "zmq_dealer"]:
            if self._zmq_socket:
                self._zmq_socket.close()
                self._zmq_socket = None
            if self._zmq_context:
                self._zmq_context.term()
                self._zmq_context = None

    def _setup_zmq_router(self):
        """Setup ZMQ ROUTER socket (server mode for orchestrator)."""
        self._zmq_context = zmq.Context()
        self._zmq_socket = self._zmq_context.socket(zmq.ROUTER)
        assert self._zmq_socket is not None
        self._zmq_socket.setsockopt(zmq.LINGER, 0)  # Don't wait on close
        self._zmq_socket.bind(self.zmq_address)

    def _setup_zmq_dealer(self):
        """Setup ZMQ DEALER socket (client mode for CLI/web)."""
        self._zmq_context = zmq.Context()
        self._zmq_socket = self._zmq_context.socket(zmq.DEALER)
        assert self._zmq_socket is not None
        self._zmq_socket.setsockopt(zmq.LINGER, 0)
        self._zmq_socket.connect(self.zmq_address)

    def _send_zmq(self, target: str, msg: ServiceMessage) -> None:
        """Send message via ZMQ socket.

        For ROUTER: sends with client identity (must be set by _receive_zmq).
        For DEALER: sends without identity frame.
        """
        if not self._zmq_socket:
            return

        msg_json = msg.to_json()

        try:
            if self.a_type == "zmq_router":
                # ROUTER: Reply to last client (identity set by _receive_zmq)
                if not hasattr(self, "_last_identity") or not self._last_identity:
                    raise RuntimeError(
                        "ROUTER: no client identity for reply. Must receive before send."
                    )

                self._zmq_socket.send_multipart(
                    [self._last_identity, b"", msg_json.encode()]
                )
            else:  # zmq_dealer
                self._zmq_socket.send_string(msg_json)
        except zmq.Again:
            # Would block, skip this message
            pass

    def _receive_zmq(self, timeout: Optional[float]) -> Optional[ServiceMessage]:
        """Receive message via ZMQ socket.

        For ROUTER: receives with client identity as first frame, stores it.
        For DEALER: receives without identity frame.

        Returns the ServiceMessage or None if timeout.
        """
        if not self._zmq_socket:
            return None

        # Convert timeout to milliseconds for ZMQ
        timeout_ms = int(timeout * 1000) if timeout is not None else -1

        try:
            if self._zmq_socket.poll(timeout_ms, zmq.POLLIN):
                if self.a_type == "zmq_router":
                    # ROUTER receives: [identity, message] from DEALER
                    # Note: DEALER doesn't send empty delimiter frame
                    frames = self._zmq_socket.recv_multipart()
                    if len(frames) >= 2:
                        self._last_identity = frames[0]  # Store for reply
                        msg_json = frames[1].decode()
                        msg_dict = json.loads(msg_json)

                        # Reconstruct ServiceMessage
                        timestamp = msg_dict.get("timestamp")
                        if isinstance(timestamp, str):
                            timestamp = datetime.fromisoformat(timestamp)

                        return ServiceMessage(
                            sender=msg_dict["sender"],
                            type=msg_dict["event_name"],
                            payload=msg_dict["payload"],
                            timestamp=timestamp,
                        )
                else:  # zmq_dealer
                    # DEALER receives: [empty_delimiter, message] from ROUTER
                    # (ZMQ removes the identity frame automatically)
                    frames = self._zmq_socket.recv_multipart()

                    # Skip empty delimiter if present
                    if len(frames) == 2 and frames[0] == b"":
                        msg_json = frames[1].decode()
                    elif len(frames) == 1:
                        msg_json = frames[0].decode()
                    else:
                        return None

                    msg_dict = json.loads(msg_json)

                    timestamp = msg_dict.get("timestamp")
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp)

                    return ServiceMessage(
                        sender=msg_dict["sender"],
                        type=msg_dict["event_name"],
                        payload=msg_dict["payload"],
                        timestamp=timestamp,
                    )
        except zmq.Again:
            pass
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

        return None
