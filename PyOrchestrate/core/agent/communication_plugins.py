"""
Communication plugins module.
"""

import zmq
import requests
import redis


class ZeroMQPlugin(CommunicationPlugin):
    """
    ZeroMQ communication plugin.

    This plugin provides communication using ZeroMQ sockets.

    Attributes:
        context (zmq.Context): The ZeroMQ context.
        socket (zmq.Socket): The ZeroMQ socket.
    """

    def __init__(self, address: str, socket_type: int):
        """
        Initializes the ZeroMQPlugin.

        Args:
            address (str): The address to bind/connect the socket.
            socket_type (int): The type of ZeroMQ socket (e.g., zmq.REQ, zmq.REP).
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(socket_type)
        self.socket.connect(address)

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

    def send(self, message: str):
        """
        Sends a message using ZeroMQ.

        Args:
            message (str): The message to send.
        """
        self.socket.send_string(message)

    def receive(self) -> str:
        """
        Receives a message using ZeroMQ.

        Returns:
            str: The received message.
        """
        return self.socket.recv_string()


class HTTPPlugin(CommunicationPlugin):
    """
    HTTP communication plugin.

    This plugin provides communication using HTTP requests.

    Attributes:
        url (str): The URL for HTTP requests.
    """

    def __init__(self, url: str):
        """
        Initializes the HTTPPlugin.

        Args:
            url (str): The URL for HTTP requests.
        """
        self.url = url

    def initialize(self):
        """
        Initializes the HTTP plugin.
        """
        pass

    def execute(self):
        """
        Executes the HTTP plugin's core logic.
        """
        pass

    def finalize(self):
        """
        Finalizes the HTTP plugin.
        """
        pass

    def send(self, message: str):
        """
        Sends a message using HTTP POST request.

        Args:
            message (str): The message to send.
        """
        requests.post(self.url, data=message)

    def receive(self) -> str:
        """
        Receives a message using HTTP GET request.

        Returns:
            str: The received message.
        """
        response = requests.get(self.url)
        return response.text


class RedisPubSubPlugin(CommunicationPlugin):
    """
    Redis Pub/Sub communication plugin.

    This plugin provides communication using Redis Pub/Sub.

    Attributes:
        redis_client (redis.Redis): The Redis client.
        channel (str): The Redis channel for Pub/Sub.
    """

    def __init__(self, host: str, port: int, channel: str):
        """
        Initializes the RedisPubSubPlugin.

        Args:
            host (str): The Redis server host.
            port (int): The Redis server port.
            channel (str): The Redis channel for Pub/Sub.
        """
        self.redis_client = redis.Redis(host=host, port=port)
        self.channel = channel

    def initialize(self):
        """
        Initializes the Redis Pub/Sub plugin.
        """
        self.pubsub = self.redis_client.pubsub()
        self.pubsub.subscribe(self.channel)

    def execute(self):
        """
        Executes the Redis Pub/Sub plugin's core logic.
        """
        pass

    def finalize(self):
        """
        Finalizes the Redis Pub/Sub plugin.
        """
        self.pubsub.unsubscribe()
        self.redis_client.close()

    def send(self, message: str):
        """
        Sends a message using Redis Pub/Sub.

        Args:
            message (str): The message to send.
        """
        self.redis_client.publish(self.channel, message)

    def receive(self) -> str:
        """
        Receives a message using Redis Pub/Sub.

        Returns:
            str: The received message.
        """
        message = self.pubsub.get_message()
        if message:
            return message['data'].decode('utf-8')
        return ""


class FileBasedPlugin(CommunicationPlugin):
    """
    File-based communication plugin.

    This plugin provides communication using file-based message passing.

    Attributes:
        file_path (str): The file path for message passing.
    """

    def __init__(self, file_path: str):
        """
        Initializes the FileBasedPlugin.

        Args:
            file_path (str): The file path for message passing.
        """
        self.file_path = file_path

    def initialize(self):
        """
        Initializes the file-based plugin.
        """
        pass

    def execute(self):
        """
        Executes the file-based plugin's core logic.
        """
        pass

    def finalize(self):
        """
        Finalizes the file-based plugin.
        """
        pass

    def send(self, message: str):
        """
        Sends a message by writing to a file.

        Args:
            message (str): The message to send.
        """
        with open(self.file_path, 'w') as file:
            file.write(message)

    def receive(self) -> str:
        """
        Receives a message by reading from a file.

        Returns:
            str: The received message.
        """
        with open(self.file_path, 'r') as file:
            return file.read()
