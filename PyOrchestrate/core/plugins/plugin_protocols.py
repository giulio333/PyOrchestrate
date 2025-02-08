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


class Plugin:
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
        self.context = zmq.Context()
        self.socket_type = socket_type
        self.subscribe_topic = subscribe_topic
        self.address = address

    def initialize(self):
        """
        Initializes the ZeroMQ plugin.

        Performs a basic check on the socket type.
        """

        if self.socket_type == zmq.PUB:
            self.socket = self.context.socket(zmq.PUB)
            self.socket.bind(self.address)
        elif self.socket_type == zmq.SUB:
            self.socket = self.context.socket(zmq.SUB)
            self.socket.connect(self.address)

            self.socket.setsockopt(zmq.SUBSCRIBE, self.subscribe_topic)

        else:
            raise ValueError("Unsupported socket type for ZeroMQPubSub plugin.")

    def finalize(self):
        """
        Finalizes the ZeroMQ plugin.
        """
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
        """
        Sends a message using ZeroMQ.

        Args:
            message: The message to send.
            topic: The topic to send the message to.

        Returns:
            (zmq.MessageTracker | None): The message tracker object allows you to track all of the 0MQ usages of a message.
        """
        return self.socket.send_multipart([topic, message])

    def setsockopt(self, option, value):
        """
        Sets a socket option.

        Args:
            option: The option to set.
            value: The value to set.
        """
        self.socket.setsockopt(option, value)


class CommunicationPlugin:

    zmq: ZeroMQPubSub | Plugin | None = None
