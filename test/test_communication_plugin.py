import unittest
import zmq
import time
from PyOrchestrate.core.plugins.communication_plugins import ZeroMQPubSub


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


if __name__ == "__main__":
    unittest.main()
