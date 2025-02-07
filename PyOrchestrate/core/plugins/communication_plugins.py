"""
Communication plugins module.
"""

import zmq
import requests
from .plugin_protocols import CommunicationPlugin


class ZeroMQPubSub(CommunicationPlugin):
    """
    ZeroMQ Pub/Sub communication plugin.

    This plugin provides communication using ZeroMQ Pub/Sub sockets.

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

        Args:
            address (str): The address to bind/connect the socket.
            socket_type (int): The type of ZeroMQ socket (e.g., zmq.REQ, zmq.REP, zmq.PUB, zmq.SUB).
            subscribe_topic (bytes): The topic to subscribe to (only for zmq.SUB). Defaults to b"" (all topics).
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(socket_type)

        if socket_type in [zmq.PUB, zmq.REP]:
            # Server sockets bind to the address
            self.socket.bind(address)
        elif socket_type in [zmq.SUB, zmq.REQ]:
            # Client sockets connect to the address
            self.socket.connect(address)

            # Configure topic filter if the socket is SUB
            if socket_type == zmq.SUB:
                self.socket.setsockopt(zmq.SUBSCRIBE, subscribe_topic)
        else:
            raise ValueError("Unsupported socket type for ZeroMQPlugin")

    def initialize(self):
        """
        Initializes the ZeroMQ plugin.
        """
        pass

    def execute(self):
        """
        Executes the ZeroMQ plugin's core logic.
        """
        pass

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
