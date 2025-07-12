import zmq
from enum import IntEnum
from PyOrchestrate.core.plugins.plugin_protocols import PluginProtocol


class SocketType(IntEnum):
    """
    Enum for ZeroMQ socket types.

    Attributes:
        PUB (int): Publish socket type.
        SUB (int): Subscribe socket type.
        REQ (int): Request socket type.
        REP (int): Reply socket type.
    """

    PUB = zmq.PUB
    SUB = zmq.SUB
    REQ = zmq.REQ
    REP = zmq.REP
    PUSH = zmq.PUSH
    PULL = zmq.PULL


class ZeroMQPubSub(PluginProtocol):
    """
    ZeroMQ Pub/Sub communication plugin.

    This plugin provides communication using ZeroMQ Pub/Sub sockets.

    Example:
        >>> from PyOrchestrate.core.plugins.com import ZeroMQPubSub, SocketType
        >>> zmq_plugin = ZeroMQPubSub("tcp://localhost:5555", SocketType.PUB)
        >>> zmq_plugin.initialize()
        >>> zmq_plugin.send(b"Hello, World!")

    Attributes:
        context (zmq.Context): The ZeroMQ context.
        socket (zmq.Socket): The ZeroMQ socket.

    Methods:
        initialize: Initializes the ZeroMQ plugin.
        finalize: Finalizes the ZeroMQ plugin.
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
            socket_type (int): The type of ZeroMQ socket (e.g., SocketType.PUB, SocketType.SUB).
            subscribe_topic (bytes): The topic to subscribe to (only for SocketType.SUB). Defaults to b"" (all topics).
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

        if self.socket_type == SocketType.PUB:
            self._socket = self.context.socket(SocketType.PUB)
            self._socket.bind(self.address)
        elif self.socket_type == SocketType.SUB:
            self._socket = self.context.socket(SocketType.SUB)
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


class ZeroMQReqRep(PluginProtocol):
    """
    ZeroMQ REQ/REP communication plugin.

    This plugin provides communication using ZeroMQ REQ/REP sockets.

    Example:
        >>> from PyOrchestrate.core.plugins.com import ZeroMQReqRep, SocketType
        >>> reqrep = ZeroMQReqRep("tcp://localhost:5555", SocketType.REQ)
        >>> reqrep.initialize()
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
            socket_type (int): The type of ZeroMQ socket (e.g., SocketType.REQ, SocketType.REP).
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

        if self.socket_type == SocketType.REQ:
            self._socket = self.context.socket(SocketType.REQ)
            self._socket.connect(self.address)
        elif self.socket_type == SocketType.REP:
            self._socket = self.context.socket(SocketType.REP)
            self._socket.bind(self.address)
        else:
            raise ValueError("Unsupported socket type for ZeroMQReqRep plugin.")

        self._initialized = True

        return self

    def send(self, message: bytes) -> None:
        """
        Sends a message using ZeroMQ.

        For SocketType.REQ, sends the request.
        For SocketType.REP, sends the reply.
        """
        self.socket.send(message)

    def recv(self) -> bytes:
        """
        Receives a message using ZeroMQ.

        For SocketType.REQ, receives the reply.
        For SocketType.REP, receives the request.
        """
        return self.socket.recv()

    def finalize(self):
        """
        Finalizes the ZeroMQ plugin.
        """
        self.socket.close()
        self.context.term()
        self._initialized = False


class ZeroMQPushPull(PluginProtocol):
    """
    ZeroMQ PUSH/PULL communication plugin.

    This plugin provides communication using ZeroMQ PUSH/PULL sockets for
    distributed pipeline processing.

    Example:
        >>> # Producer (PUSH)
        >>> from PyOrchestrate.core.plugins.com import ZeroMQPushPull, SocketType
        >>> push = ZeroMQPushPull("tcp://localhost:5555", SocketType.PUSH)
        >>> push.initialize()
        >>> push.send(b"Task data")
        >>>
        >>> # Worker (PULL)
        >>> pull = ZeroMQPushPull("tcp://localhost:5555", SocketType.PULL)
        >>> pull.initialize()
        >>> task = pull.recv()

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
        self,
        address: str,
        socket_type: int,
        context: zmq.Context | None = None,
        hwm: int | None = None,
    ):
        """
        Initializes the ZeroMQ PUSH/PULL plugin.

        Args:
            address (str): The address to bind/connect the socket.
            socket_type (int): The type of ZeroMQ socket (SocketType.PUSH or SocketType.PULL).
            context (zmq.Context, optional): The ZeroMQ context. Defaults to None.
            hwm (int, optional): The high water mark for the socket. Defaults to None.
        """
        self.address = address
        self.socket_type = socket_type
        self._socket: zmq.Socket | None = None
        self.context = context if context is not None else zmq.Context()
        self.hwm = hwm

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

        For SocketType.PUSH, the socket binds to the address.
        For SocketType.PULL, the socket connects to the address.
        """
        if self._initialized:
            return self

        if self.socket_type == SocketType.PUSH:
            self._socket = self.context.socket(SocketType.PUSH)
            self._socket.bind(self.address)
            if self.hwm:
                self._socket.setsockopt(zmq.SNDHWM, self.hwm)
        elif self.socket_type == SocketType.PULL:
            self._socket = self.context.socket(SocketType.PULL)
            if self.hwm:
                self._socket.setsockopt(zmq.RCVHWM, self.hwm)
            self._socket.connect(self.address)
        else:
            raise ValueError("Unsupported socket type for ZeroMQPushPull plugin.")

        self._initialized = True

        return self

    def send(self, message: bytes, blocking: bool = True) -> None:
        """
        Sends a message using ZeroMQ PUSH socket.

        This method is only valid for SocketType.PUSH sockets.

        Args:
            message (bytes): The message to be sent.
            blocking (bool, optional): If True, the send operation blocks until complete.
                                      If False, the send returns immediately and may raise zmq.error.Again
                                      if the message cannot be queued. Defaults to True.

        Raises:
            RuntimeError: If used with a SocketType.PULL socket.
            zmq.error.Again: If the message cannot be queued and blocking is False.
        """
        if self.socket_type != SocketType.PUSH:
            raise RuntimeError("Cannot send with a SocketType.PULL socket.")

        if blocking:
            self.socket.send(message)
        else:
            self.socket.send(message, zmq.NOBLOCK)

    def recv(self) -> bytes:
        """
        Receives a message using ZeroMQ PULL socket.

        This method is only valid for SocketType.PULL sockets.

        Returns:
            bytes: The received message.

        Raises:
            RuntimeError: If used with a SocketType.PUSH socket.
        """
        if self.socket_type != SocketType.PULL:
            raise RuntimeError("Cannot receive with a SocketType.PUSH socket.")
        return self.socket.recv()

    def finalize(self):
        """
        Finalizes the ZeroMQ plugin.
        """
        self.socket.close()
        self.context.term()
        self._initialized = False
