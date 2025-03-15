import unittest
import zmq
import time
import requests
import threading
import websocket
from PyOrchestrate.core.plugins import ZeroMQPubSub, HTTPPlugin, WebSocketPlugin


class TestZeroMQPubSub(unittest.TestCase):

    def test_invalid_socket_type(self):
        # Only zmq.PUB and zmq.SUB are supported.
        with self.assertRaises(ValueError):
            plugin = ZeroMQPubSub("tcp://127.0.0.1:5555", zmq.REQ)
            plugin.initialize()

    def test_pub_sub_send_receive(self):
        address = "tcp://127.0.0.1:5556"

        # Initialize the subscriber first.
        sub = ZeroMQPubSub(address, zmq.SUB, subscribe_topic=b"")
        sub.initialize()
        # Sleep to allow the subscription to register.
        time.sleep(1)

        # Now initialize the publisher.
        pub = ZeroMQPubSub(address, zmq.PUB)
        pub.initialize()
        # Additional sleep to ensure that the connection is established.
        time.sleep(1)

        message = b"Hello, ZeroMQ!"
        pub.send(message)
        # Sleep to allow the message to propagate.
        time.sleep(1)
        received_message: bytes = sub.recv()
        self.assertEqual(received_message, message)

        # Finalize both plugins.
        pub.finalize()
        sub.finalize()

    def test_pub_sub_subscribe_topic(self):
        address = "tcp://127.0.0.1:5557"
        topic = b"test"

        # Initialize the subscriber with a specific topic.
        sub = ZeroMQPubSub(address, zmq.SUB, topic)
        sub.initialize()

        time.sleep(1)

        pub = ZeroMQPubSub(address, zmq.PUB)
        pub.initialize()

        time.sleep(1)

        message = b"Hello, ZeroMQ with topic!"
        pub.send(message, topic)

        time.sleep(1)
        received_message: bytes = sub.recv()
        self.assertEqual(received_message, message)

        self.assertTrue(received_message.startswith(b"Hello"))

        pub.finalize()
        sub.finalize()


class TestHTTPPlugin(unittest.TestCase):

    def setUp(self):
        self.base_url = "http://localhost:8000"
        self.plugin = HTTPPlugin(self.base_url)
        self.plugin.initialize()

    def tearDown(self):
        self.plugin.finalize()

    def test_send(self):
        response = self.plugin.send("Hello, HTTP!")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "Received: Hello, HTTP!")

    def test_recv(self):
        response_text = self.plugin.recv()
        self.assertEqual(response_text, "Hello from server!")


class TestWebSocketPlugin(unittest.TestCase):

    def setUp(self):
        self.url = "ws://localhost:8000"
        self.plugin = WebSocketPlugin(self.url)
        self.plugin.initialize()

    def tearDown(self):
        self.plugin.finalize()

    def test_send(self):
        self.plugin.send("Hello, WebSocket!")
        response = self.plugin.recv()
        self.assertEqual(response, "Received: Hello, WebSocket!")

    def test_recv(self):
        response = self.plugin.recv()
        self.assertEqual(response, "Hello from WebSocket server!")


if __name__ == "__main__":
    unittest.main()
