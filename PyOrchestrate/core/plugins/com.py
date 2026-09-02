import zmq
from abc import abstractmethod
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
        PUSH (int): Push socket type.
        PULL (int): Pull socket type.
        ROUTER (int): Router socket type.
        DEALER (int): Dealer socket type.
        PAIR (int): Pair socket type.
    """

    PUB = zmq.PUB
    SUB = zmq.SUB
    REQ = zmq.REQ
    REP = zmq.REP
    PUSH = zmq.PUSH
    PULL = zmq.PULL
    ROUTER = zmq.ROUTER
    DEALER = zmq.DEALER
    PAIR = zmq.PAIR


class ZeroMQSocketPlugin(PluginProtocol):
    """
    Shared behaviour of the plugins that own a single ZeroMQ socket.

    Every ZeroMQ plugin in this module holds one socket, hands it out only once
    `initialize()` has run, sends and receives whole messages with an optional
    non-blocking flag, and closes both socket and context on `finalize()`. Only
    `initialize()` genuinely differs between them — which socket type to create,
    whether to bind or connect, which options to set — so that is the one method
    subclasses must implement.

    Subclass it to support a socket type this module does not cover:

    ```python
    from PyOrchestrate.core.plugins.com import SocketType, ZeroMQSocketPlugin


    class ZeroMQXPubXSub(ZeroMQSocketPlugin):

        def initialize(self):
            if self._initialized:
                return
            self._socket = self.context.socket(zmq.XPUB)
            self._socket.bind(self.address)
            self._initialized = True
    ```

    Attributes:
        address (str): The address the socket binds or connects to.
        context (zmq.Context): The ZeroMQ context.
        hwm (int | None): The high water mark applied by `initialize()`, when
            the subclass supports one.
        socket (zmq.Socket): The ZeroMQ socket. Raises until `initialize()` runs.
    """

    def __init__(
        self,
        address: str,
        context: zmq.Context | None = None,
        hwm: int | None = None,
    ):
        """
        Stores the connection parameters without touching the network.

        No socket exists until `initialize()` is called, so building a plugin is
        safe in a parent process that will fork.

        A context passed in belongs to the caller: `finalize()` closes the
        socket but leaves that context running, so several plugins can share
        the single context per process the warning below asks for.

        Warning:
            Ensure that one process has only one zmq.Context instance.

        Args:
            address (str): The address to bind/connect the socket.
            context (zmq.Context, optional): The ZeroMQ context. Defaults to None,
                which creates one owned by the plugin.
            hwm (int, optional): The high water mark for the socket. Defaults to None.
        """
        self.address = address
        self.context = context if context is not None else zmq.Context()
        self.hwm = hwm

        self._owns_context = context is None
        self._socket: zmq.Socket | None = None
        self._initialized = False

    @property
    def socket(self) -> zmq.Socket:
        if not self._socket:
            raise RuntimeError(
                "Socket not initialized. Did you forget to call initialize?"
            )
        return self._socket

    def setsockopt(self, option, value) -> None:
        """
        Sets a socket option on the underlying socket.

        Args:
            option: The ZeroMQ socket option (e.g. `zmq.SUBSCRIBE`).
            value: The value to set.

        Raises:
            RuntimeError: If `initialize()` has not run.
        """
        self.socket.setsockopt(option, value)

    @abstractmethod
    def initialize(self):
        """
        Creates the socket and binds or connects it.

        Implementations must return early when `self._initialized` is already
        true, and set it once the socket is ready.
        """

    def send(self, message: bytes, blocking: bool = True) -> None:
        """
        Sends a message using ZeroMQ.

        Args:
            message (bytes): The message to be sent.
            blocking (bool, optional): If True, the operation blocks until
                complete. If False, returns immediately and may raise
                zmq.error.Again if the message cannot be queued. Defaults to True.

        Raises:
            zmq.error.Again: If the message cannot be queued and blocking is False.
        """
        if blocking:
            self.socket.send(message)
        else:
            self.socket.send(message, zmq.NOBLOCK)

    def recv(self, blocking: bool = True) -> bytes:
        """
        Receives a message using ZeroMQ.

        - If blocking is True, the receive operation blocks until a message arrives.
        - If blocking is False, the receive returns immediately and may raise zmq.error.Again
          if no message is available.

        Args:
            blocking (bool, optional): Whether to block or not. Defaults to True.

        Returns:
            bytes: The received message.

        Raises:
            zmq.error.Again: If no message is available and blocking is False.
        """
        if blocking:
            return self.socket.recv()
        else:
            return self.socket.recv(zmq.NOBLOCK)

    def finalize(self):
        """
        Finalizes the ZeroMQ plugin.

        Closes the socket, and terminates the context only when the plugin
        created it. A context received from the caller is left alone:
        `zmq.Context.term()` blocks until every socket in the context is
        closed, so terminating a shared one hung the first plugin to finalize
        on the sockets its siblings still held, and poisoned the context for
        them in the meantime.

        Does nothing when `initialize()` never ran or failed, since `socket`
        would raise.
        """
        if not self._initialized:
            return

        self.socket.close()
        if self._owns_context:
            self.context.term()
        self._initialized = False


class ZeroMQPubSub(ZeroMQSocketPlugin):
    """
    ZeroMQ Pub/Sub communication plugin.

    This plugin provides communication using ZeroMQ Pub/Sub sockets.

    Messages travel as two frames, topic then payload: `send()` prepends the
    topic and `recv()` drops it, returning the payload alone.

    Example:
        >>> from PyOrchestrate.core.plugins.com import ZeroMQPubSub, SocketType
        >>> zmq_plugin = ZeroMQPubSub("tcp://localhost:5555", SocketType.PUB)
        >>> zmq_plugin.initialize()
        >>> zmq_plugin.send(b"Hello, World!")

    Attributes:
        context (zmq.Context): The ZeroMQ context.
        socket (zmq.Socket): The ZeroMQ socket.

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
            socket_type (int): The type of ZeroMQ socket
                (e.g., SocketType.PUB, SocketType.SUB).
            subscribe_topic (bytes): The topic to subscribe to
                (only for SocketType.SUB). Defaults to b"" (all topics).
            context (zmq.Context, optional): The ZeroMQ context.
                Defaults to None.
        """
        super().__init__(address, context)
        self.socket_type = socket_type
        self.subscribe_topic = subscribe_topic

    def initialize(self):
        """
        Initializes the ZeroMQ plugin.

        For SocketType.PUB, binds to the address.
        For SocketType.SUB, connects to the address and subscribes to the topic.
        """
        if self._initialized:
            return

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

    def recv(self, blocking: bool = True) -> bytes:
        """
        Receives a message using ZeroMQ, discarding the topic frame.

        - If blocking is True, the receive operation blocks until a message arrives.
        - If blocking is False, the receive returns immediately and may raise zmq.error.Again
          if no message is available.

        Args:
            blocking (bool, optional): Whether to block or not. Defaults to True.

        Returns:
            bytes: The received message.

        Raises:
            zmq.error.Again: If no message is available and blocking is False.
        """
        if blocking:
            topic, message = self.socket.recv_multipart()
        else:
            topic, message = self.socket.recv_multipart(zmq.NOBLOCK)
        return message

    def send(
        self, message: bytes, topic: bytes = b"", blocking: bool = True
    ) -> zmq.MessageTracker | None:
        """
        Sends a message using ZeroMQ, prefixed by its topic frame.

        Args:
            message (bytes): The message to be sent.
            topic (bytes, optional): The topic to use for the message. Defaults to b"".
            blocking (bool, optional): If True, the operation blocks until
                complete. If False, returns immediately and may raise
                zmq.error.Again if the message cannot be queued. Defaults to True.

        Returns:
            (zmq.MessageTracker | None): The result of the send operation or None.

        Raises:
            zmq.error.Again: If the message cannot be queued and blocking is False.
        """
        if blocking:
            return self.socket.send_multipart([topic, message])
        else:
            return self.socket.send_multipart([topic, message], zmq.NOBLOCK)


class ZeroMQReqRep(ZeroMQSocketPlugin):
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
        super().__init__(address, context)
        self.socket_type = socket_type

    def initialize(self):
        """
        Initializes the ZeroMQ plugin.

        For zmq.REQ, connects to the address.
        For zmq.REP, binds to the address.
        """
        if self._initialized:
            return

        if self.socket_type == SocketType.REQ:
            self._socket = self.context.socket(SocketType.REQ)
            self._socket.connect(self.address)
        elif self.socket_type == SocketType.REP:
            self._socket = self.context.socket(SocketType.REP)
            self._socket.bind(self.address)
        else:
            raise ValueError("Unsupported socket type for ZeroMQReqRep plugin.")

        self._initialized = True


class ZeroMQPushPull(ZeroMQSocketPlugin):
    """
    ZeroMQ PUSH/PULL communication plugin.

    This plugin provides communication using ZeroMQ PUSH/PULL sockets for
    distributed pipeline processing.

    The socket is one-directional: `send()` rejects a PULL socket and `recv()`
    rejects a PUSH one.

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
        super().__init__(address, context, hwm)
        self.socket_type = socket_type

    def initialize(self):
        """
        Initializes the ZeroMQ plugin.

        For SocketType.PUSH, the socket binds to the address.
        For SocketType.PULL, the socket connects to the address.
        """
        if self._initialized:
            return

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

    def send(self, message: bytes, blocking: bool = True) -> None:
        """
        Sends a message using ZeroMQ PUSH socket.

        This method is only valid for SocketType.PUSH sockets.

        Args:
            message (bytes): The message to be sent.
            blocking (bool, optional): If True, the operation blocks until
                complete. If False, returns immediately and may raise
                zmq.error.Again if the message cannot be queued. Defaults to True.

        Raises:
            RuntimeError: If used with a SocketType.PULL socket.
            zmq.error.Again: If the message cannot be queued and blocking is False.
        """
        if self.socket_type != SocketType.PUSH:
            raise RuntimeError("Cannot send with a SocketType.PULL socket.")

        super().send(message, blocking)

    def recv(self, blocking: bool = True) -> bytes:
        """
        Receives a message using ZeroMQ PULL.

        - If blocking is True, the receive operation blocks until a message arrives.
        - If blocking is False, the receive returns immediately and may raise zmq.error.Again
          if no message is available.

        Args:
            blocking (bool, optional): Whether to block or not. Defaults to True.

        Returns:
            bytes: The received message.

        Raises:
            RuntimeError: If used with a PUSH socket.
            zmq.error.Again: If no message is available and blocking is False.
        """
        if self.socket_type != SocketType.PULL:
            raise RuntimeError("Cannot receive with a SocketType.PUSH socket.")

        return super().recv(blocking)


class ZeroMQRouterDealer(ZeroMQSocketPlugin):
    """
    ZeroMQ ROUTER/DEALER communication plugin.

    This plugin provides advanced request/reply routing using ZeroMQ ROUTER/DEALER sockets.
    ROUTER sockets can handle multiple clients and route messages based on client identity.
    DEALER sockets can connect to multiple services and load balance requests.

    A ROUTER socket needs the identity frame that `send_multipart()` and
    `recv_multipart()` expose; `send()` and `recv()` handle the single-frame case
    a DEALER uses.

    Example:
        >>> # Server side with ROUTER
        >>> router = ZeroMQRouterDealer("tcp://*:5555", SocketType.ROUTER)
        >>> router.initialize()
        >>> identity, message = router.recv_multipart()
        >>> router.send_multipart([identity, b"Response"])
        >>>
        >>> # Client side with DEALER
        >>> dealer = ZeroMQRouterDealer("tcp://localhost:5555", SocketType.DEALER)
        >>> dealer.initialize()
        >>> dealer.send(b"Request")
        >>> response = dealer.recv()

    Attributes:
        context (zmq.Context): The ZeroMQ context.
        socket (zmq.Socket): The ZeroMQ socket.

    """

    def __init__(
        self,
        address: str,
        socket_type: int,
        context: zmq.Context | None = None,
        identity: bytes | None = None,
        hwm: int | None = None,
    ):
        """
        Initializes the ZeroMQ ROUTER/DEALER plugin.

        Args:
            address (str): The address to bind/connect the socket.
            socket_type (int): The type of ZeroMQ socket

                (SocketType.ROUTER or SocketType.DEALER).
            context (zmq.Context, optional): The ZeroMQ context. Defaults to None.
            identity (bytes, optional): The identity for DEALER socket. Defaults to None.
            hwm (int, optional): The high water mark for the socket. Defaults to None.
        """
        super().__init__(address, context, hwm)
        self.socket_type = socket_type
        self.identity = identity

    def initialize(self):
        """
        Initializes the ZeroMQ plugin.

        For SocketType.ROUTER, the socket binds to the address.
        For SocketType.DEALER, the socket connects to the address.
        """
        if self._initialized:
            return

        if self.socket_type == SocketType.ROUTER:
            self._socket = self.context.socket(SocketType.ROUTER)
            if self.hwm:
                self._socket.setsockopt(zmq.RCVHWM, self.hwm)
                self._socket.setsockopt(zmq.SNDHWM, self.hwm)
            self._socket.bind(self.address)
        elif self.socket_type == SocketType.DEALER:
            self._socket = self.context.socket(SocketType.DEALER)
            if self.identity:
                self._socket.setsockopt(zmq.IDENTITY, self.identity)
            if self.hwm:
                self._socket.setsockopt(zmq.RCVHWM, self.hwm)
                self._socket.setsockopt(zmq.SNDHWM, self.hwm)
            self._socket.connect(self.address)
        else:
            raise ValueError("Unsupported socket type for ZeroMQRouterDealer plugin.")

        self._initialized = True

    def send_multipart(self, message_parts: list[bytes], blocking: bool = True) -> None:
        """
        Sends a multipart message using ZeroMQ.

        This is particularly useful for ROUTER sockets which need to route messages
        based on client identity.

        Args:
            message_parts (list[bytes]): The list of message parts

                to be sent.
            blocking (bool, optional): If True, the operation blocks until
                complete. If False, returns immediately and may raise
                zmq.error.Again if the message cannot be queued. Defaults to True.

        Raises:
            zmq.error.Again: If the message cannot be queued and blocking is False.
        """
        if blocking:
            self.socket.send_multipart(message_parts)
        else:
            self.socket.send_multipart(message_parts, zmq.NOBLOCK)

    def recv_multipart(self, blocking: bool = True) -> list[bytes]:
        """
        Receives a multipart message using ZeroMQ.

        This is particularly useful for ROUTER sockets which receive messages
        with client identity as the first part.

        Args:
            blocking (bool, optional): If True, the receive operation blocks until a
                message arrives. If False, the receive returns immediately and may
                raise zmq.error.Again if no message is available. Defaults to True.

        Returns:
            list[bytes]: The list of received message parts.

        Raises:
            zmq.error.Again: If no message is available and blocking is False.
        """
        if blocking:
            return self.socket.recv_multipart()
        else:
            return self.socket.recv_multipart(zmq.NOBLOCK)


class ZeroMQPair(ZeroMQSocketPlugin):
    """
    ZeroMQ PAIR communication plugin.

    This plugin provides bidirectional communication using ZeroMQ PAIR sockets.
    PAIR sockets are designed for connecting two peers exclusively.

    There is no socket type to choose: `bind` decides which of the two peers
    binds and which connects.

    Example:
        >>> # Peer A
        >>> pair_a = ZeroMQPair("tcp://*:5555")
        >>> pair_a.initialize()
        >>> pair_a.send(b"Hello from A")
        >>> message = pair_a.recv()
        >>>
        >>> # Peer B
        >>> pair_b = ZeroMQPair("tcp://localhost:5555", bind=False)
        >>> pair_b.initialize()
        >>> message = pair_b.recv()
        >>> pair_b.send(b"Hello from B")

    Attributes:
        context (zmq.Context): The ZeroMQ context.
        socket (zmq.Socket): The ZeroMQ socket.

    """

    def __init__(
        self,
        address: str,
        bind: bool = True,
        context: zmq.Context | None = None,
        hwm: int | None = None,
    ):
        """
        Initializes the ZeroMQ PAIR plugin.

        Args:
            address (str): The address to bind/connect the socket.
            bind (bool, optional): If True, binds to the address.

                If False, connects to the address. Defaults to True.
            context (zmq.Context, optional): The ZeroMQ context. Defaults to None.
            hwm (int, optional): The high water mark for the socket. Defaults to None.
        """
        super().__init__(address, context, hwm)
        self.bind = bind

    def initialize(self):
        """
        Initializes the ZeroMQ plugin.

        Creates a PAIR socket and either binds or connects based on configuration.
        """
        if self._initialized:
            return

        self._socket = self.context.socket(SocketType.PAIR)

        if self.hwm:
            self._socket.setsockopt(zmq.RCVHWM, self.hwm)
            self._socket.setsockopt(zmq.SNDHWM, self.hwm)

        if self.bind:
            self._socket.bind(self.address)
        else:
            self._socket.connect(self.address)

        self._initialized = True


class ZeroMQPoller(PluginProtocol):
    """
    ZeroMQ Poller utility for non-blocking operations across multiple sockets.

    This utility provides polling capabilities for multiple ZeroMQ sockets,
    allowing non-blocking operations and event-driven programming.

    It owns no socket of its own, which is why it does not build on
    `ZeroMQSocketPlugin`: it watches the sockets the other plugins expose.

    Example:
        >>> # Create multiple sockets
        >>> pub = ZeroMQPubSub("tcp://*:5555", SocketType.PUB)
        >>> sub = ZeroMQPubSub("tcp://localhost:5555", SocketType.SUB)
        >>> pub.initialize()
        >>> sub.initialize()
        >>>
        >>> # Create poller and register sockets
        >>> poller = ZeroMQPoller()
        >>> poller.initialize()
        >>> poller.register(sub.socket, zmq.POLLIN)
        >>> poller.register(pub.socket, zmq.POLLOUT)
        >>>
        >>> # Poll for events
        >>> events = poller.poll(timeout=1000)  # 1 second timeout
        >>> for socket, event in events:
        >>>     if event & zmq.POLLIN:
        >>>         # Socket is ready for reading
        >>>         message = socket.recv(zmq.NOBLOCK)
        >>>     elif event & zmq.POLLOUT:
        >>>         # Socket is ready for writing
        >>>         socket.send(b"Hello", zmq.NOBLOCK)

    Attributes:
        poller (zmq.Poller): The ZeroMQ poller instance.

    """

    def __init__(self, context: zmq.Context | None = None):
        """
        Initializes the ZeroMQ Poller.

        Args:
            context (zmq.Context, optional): The ZeroMQ context. Defaults to None.
        """
        self.context = context if context is not None else zmq.Context()
        self._poller: zmq.Poller | None = None
        self._initialized = False

    @property
    def poller(self) -> zmq.Poller:
        if not self._poller:
            raise RuntimeError(
                "Poller not initialized. Did you forget to call initialize?"
            )
        return self._poller

    def initialize(self):
        """
        Initializes the ZeroMQ poller.
        """
        if self._initialized:
            return

        self._poller = zmq.Poller()
        self._initialized = True

    def register(self, socket: zmq.Socket, flags: int = zmq.POLLIN) -> None:
        """
        Registers a socket with the poller.

        Args:
            socket (zmq.Socket): The socket to register.
            flags (int, optional): The polling flags (zmq.POLLIN, zmq.POLLOUT, or both).
                                  Defaults to zmq.POLLIN.
        """
        self.poller.register(socket, flags)

    def unregister(self, socket: zmq.Socket) -> None:
        """
        Unregisters a socket from the poller.

        Args:
            socket (zmq.Socket): The socket to unregister.
        """
        self.poller.unregister(socket)

    def poll(self, timeout: int | None = None) -> list[tuple[zmq.Socket, int]]:
        """
        Polls for events on registered sockets.

        Args:
            timeout (int, optional): The timeout in milliseconds. If None, blocks indefinitely.
                                   If 0, returns immediately (non-blocking).
                                   Defaults to None.

        Returns:
            list[tuple[zmq.Socket, int]]: A list of (socket, event) tuples where
                                         event is a bitmask of zmq.POLLIN, zmq.POLLOUT, etc.
        """
        return self.poller.poll(timeout)

    def finalize(self):
        """
        Finalizes the ZeroMQ poller.
        """
        if self._poller:
            # Note: zmq.Poller doesn't have a close method, just clear registered sockets
            self._poller = None
        self._initialized = False
