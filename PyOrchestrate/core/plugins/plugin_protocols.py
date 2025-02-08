"""
plugin_protocols module.
This module defines the interfaces (protocols) that plugins must implement to be integrated
with the PyOrchestrate framework. The interfaces provide a standardized structure for:
- Plugin initialization (setup).
- Execution of the main plugin logic.
- Finalization (cleanup) after use.

The protocols defined in this module ensure that every plugin adheres to a common contract,
thus promoting consistency and interoperability within the system.
"""

import zmq
from typing import Protocol


class Plugin(Protocol):
    """
    Base protocol for all plugins.

    This protocol defines the essential methods required for managing a plugin's lifecycle:
    - initialize: Prepares the plugin by allocating resources or setting up the initial state.
    - execute: Executes the main logic of the plugin.
    - finalize: Handles cleanup and resource release.

    Developers must implement these methods to ensure proper integration with the system.
    """

    def initialize(self):
        """
        Initializes the plugin.

        Called only once at the time of plugin registration.
        Use this method to set up the necessary resources for subsequent execution.
        """
        pass

    def finalize(self):
        """
        Finalizes the plugin.

        Called at the end of the plugin lifecycle to release resources, close connections,
        or perform any other cleanup operations.
        """
        pass


class ZeroMQPubSub(Plugin):
    """
    ZeroMQ Pub/Sub communication plugin.

    This plugin provides communication using ZeroMQ Pub/Sub sockets.

    Example:
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

    def __init__(self, address: str, socket_type: int, subscribe_topic: bytes = b""):
        """
        Initializes the ZeroMQPlugin.

        Warning:
            Ensure that one process has only one zmq.Context instance. If you create multiple ZeroMQ plugins in the same
            process, they should share the same context.

        Args:
            address (str): The address to bind/connect the socket.
            socket_type (int): The type of ZeroMQ socket (e.g., zmq.REQ, zmq.REP, zmq.PUB, zmq.SUB).
            subscribe_topic (bytes): The topic to subscribe to (only for zmq.SUB). Defaults to b"" (all topics).
        """
        self._socket: zmq.Socket | None = None
        self.context = zmq.Context()
        self.socket_type = socket_type
        self.subscribe_topic = subscribe_topic
        self.address = address

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

        if self.socket_type == zmq.PUB:
            self._socket = self.context.socket(zmq.PUB)
            self._socket.bind(self.address)
        elif self.socket_type == zmq.SUB:
            self._socket = self.context.socket(zmq.SUB)
            self._socket.connect(self.address)

            self._socket.setsockopt(zmq.SUBSCRIBE, self.subscribe_topic)

        else:
            raise ValueError("Unsupported socket type for ZeroMQPubSub plugin.")

        return self

    def finalize(self):
        """
        Finalizes the ZeroMQ plugin.
        """
        if not self.socket:
            raise RuntimeError(
                "Socket not initialized. Did you forget to call initialize method?"
            )
        self.socket.close()
        self.context.term()

    def recv(self) -> bytes:
        """
        Receives a message using ZeroMQ.

        Args:
            flags (int): The flags to use for the receive operation.

        Returns:
            Any: The received message.
        """
        topic, message = self.socket.recv_multipart()
        return message

    def send(self, message: bytes, topic: bytes = b"") -> zmq.MessageTracker | None:
        return self.socket.send_multipart([topic, message])
