"""
Communication plugins module.
"""

import zmq
from .plugin_protocols import CommunicationPlugin


class ZeroMQPubSub(CommunicationPlugin):
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

    def send_string(self, message: str):
        """
        Sends a message using ZeroMQ.

        Args:
            message (str): The message to send.
        """
        self.socket.send_string(message)

    def recv_string(self) -> str:
        """
        Receives a message using ZeroMQ.

        Returns:
            str: The received message.
        """
        return self.socket.recv_string()

    def recv(self, flags: int = 0):
        """
        Receives a message using ZeroMQ.

        Args:
            flags (int): The flags to use for the receive operation.

        Returns:
            Any: The received message.
        """
        return self.socket.recv(flags)

    def send(self, message, flags: int = 0):
        """
        Sends a message using ZeroMQ.

        Args:
            message: The message to send.
            flags (int): The flags to use for the send operation.
        """
        self.socket.send(message, flags)

    def setsockopt(self, option, value):
        """
        Sets a socket option.

        Args:
            option: The option to set.
            value: The value to set.
        """
        self.socket.setsockopt(option, value)
