import zmq
from .plugin_protocols import Plugin


class ZeroMQPubSub(Plugin):
    """
    ZeroMQ Pub/Sub communication plugin.

    This plugin provides communication using ZeroMQ Pub/Sub sockets.

    Example:
        >>> from PyOrchestrate.core.plugins.com import ZeroMQPubSub
        >>> import zmq
        >>> zmq_plugin = ZeroMQPubSub("tcp://localhost:5555", zmq.PUB)
        >>> zmq_plugin.send_string("Hello, World!")

    Attributes:
        context (zmq.Context): The ZeroMQ context.
        socket (zmq.Socket): The ZeroMQ socket.

    Methods:
        initialize: Initializes the ZeroMQ plugin.
        execute: Executes the ZeroMQ plugin's core logic.
        finalize: Finalizes the ZeroMQ plugin.
        send_string: Sends a message using ZeroMQ.
        recv_string: Receives a message using ZeroMQ.
        recv: Receives a message using ZeroMQ.
        send: Sends a message using ZeroMQ.
        setsockopt: Sets a socket option.
    """

    def __init__(
        self,
        address: str,
        socket_type: int,
        subscribe_topic: bytes = b"",
        context: zmq.Context | None = None,
    ):
        """
        Initializes the ZeroMQPlugin.

        Warning:
            Ensure that one process has only one zmq.Context instance.

        Args:
            address (str): The address to bind/connect the socket.
            socket_type (int): The type of ZeroMQ socket (e.g., zmq.REQ, zmq.REP, zmq.PUB, zmq.SUB).
            subscribe_topic (bytes): The topic to subscribe to (only for zmq.SUB). Defaults to b"" (all topics).
            context (zmq.Context, optional): The ZeroMQ context. Defaults to None.
        """
        self._socket: zmq.Socket | None = None
        self.context = context if context is not None else zmq.Context()
        self.socket_type = socket_type
        self.subscribe_topic = subscribe_topic
        self.address = address

        self._initialized = False

    @property
    def socket(self) -> zmq.Socket:
        if not self._socket:
            raise RuntimeError(
                "Socket not initialized. Did you forget to call initialize method?"
            )
        return self._socket

    def setsockopt(self, option, value) -> None:
        self.socket.setsockopt(option, value)

    def initialize(self):
        """
        Initializes the ZeroMQ plugin.
        """
        if self._initialized:
            return self

        if self.socket_type == zmq.PUB:
            self._socket = self.context.socket(zmq.PUB)
            self._socket.bind(self.address)
        elif self.socket_type == zmq.SUB:
            self._socket = self.context.socket(zmq.SUB)
            self._socket.connect(self.address)

            self._socket.setsockopt(zmq.SUBSCRIBE, self.subscribe_topic)

        else:
            raise ValueError("Unsupported socket type for ZeroMQPubSub plugin.")

        self._initialized = True

        return self

    def finalize(self):
        """
        Finalizes the ZeroMQ plugin.
        """
        self.socket.close()
        self.context.term()
        self._initialized = False

    def recv(self) -> bytes:
        """
        Receives a message using ZeroMQ.

        Returns:
            bytes: The received message.
        """
        topic, message = self.socket.recv_multipart()
        return message

    def send(self, message: bytes, topic: bytes = b"") -> zmq.MessageTracker | None:
        """
        Sends a message using ZeroMQ.

        Args:
            message (bytes): The message to be sent.
            topic (bytes, optional): The topic to use for the message. Defaults to b"".

        Returns:
            (zmq.MessageTracker | None): The result of the send operation or None.
        """
        return self.socket.send_multipart([topic, message])


class ZeroMQReqRep(Plugin):
    """
    ZeroMQ REQ/REP communication plugin.

    This plugin provides communication using ZeroMQ REQ/REP sockets.

    Example:
        >>> reqrep = ZeroMQReqRep("tcp://localhost:5555", zmq.REQ)
        >>> reqrep.send(b"Hello")
        >>> reply = reqrep.recv()

    Attributes:
        context (zmq.Context): The ZeroMQ context.
        socket (zmq.Socket): The ZeroMQ socket.

    Methods:
        initialize: Initializes the ZeroMQ plugin.
        send: Sends a message using ZeroMQ.
        recv: Receives a message using ZeroMQ.
        finalize: Finalizes the ZeroMQ plugin.
    """

    def __init__(
        self, address: str, socket_type: int, context: zmq.Context | None = None
    ):
        """
        Initializes the ZeroMQ REQ/REP plugin.

        Args:
            address (str): The address to bind/connect the socket.
            socket_type (int): The type of ZeroMQ socket (e.g., zmq.REQ, zmq.REP).
            context (zmq.Context, optional): The ZeroMQ context. Defaults to None.
        """
        self.address = address
        self.socket_type = socket_type
        self._socket: zmq.Socket | None = None
        self.context = context if context is not None else zmq.Context()

        self._initialized = False

    @property
    def socket(self) -> zmq.Socket:
        if not self._socket:
            raise RuntimeError(
                "Socket not initialized. Did you forget to call initialize?"
            )
        return self._socket

    def initialize(self):
        """
        Initializes the ZeroMQ plugin.

        For zmq.REQ, connects to the address.
        For zmq.REP, binds to the address.
        """
        if self._initialized:
            return self

        if self.socket_type == zmq.REQ:
            self._socket = self.context.socket(zmq.REQ)
            self._socket.connect(self.address)
        elif self.socket_type == zmq.REP:
            self._socket = self.context.socket(zmq.REP)
            self._socket.bind(self.address)
        else:
            raise ValueError("Unsupported socket type for ZeroMQReqRep plugin.")

        self._initialized = True

        return self

    def send(self, message: bytes) -> None:
        """
        Sends a message using ZeroMQ.

        For zmq.REQ, sends the request.
        For zmq.REP, sends the reply.
        """
        self.socket.send(message)

    def recv(self) -> bytes:
        """
        Receives a message using ZeroMQ.

        For zmq.REQ, receives the reply.
        For zmq.REP, receives the request.
        """
        return self.socket.recv()

    def finalize(self):
        """
        Finalizes the ZeroMQ plugin.
        """
        self.socket.close()
        self.context.term()
        self._initialized = False
