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

        message = "Hello, ZeroMQ!"
        pub.send_string(message)
        # Sleep to allow the message to propagate.
        time.sleep(1)
        received_message: str = sub.recv_string()
        self.assertEqual(received_message, message)

        # Finalize both plugins.
        pub.finalize()
        sub.finalize()

    def test_send_and_recv_methods(self):
        # This test verifies that send and recv work for binary messages.
        address = "tcp://127.0.0.1:5557"

        # Set up subscriber with a specific subscription topic.
        topic = b"topic1"
        sub = ZeroMQPubSub(address, zmq.SUB, subscribe_topic=topic)
        sub.initialize()
        time.sleep(1)

        # Publisher setup.
        pub = ZeroMQPubSub(address, zmq.PUB)
        pub.initialize()
        time.sleep(1)

        # Construct a message that includes the topic.
        message = topic + b" " + b"Binary test message."
        pub.send(message)
        time.sleep(1)
        received_message = sub.recv()
        self.assertTrue(received_message.startswith(topic))

        pub.finalize()
        sub.finalize()


if __name__ == "__main__":
    unittest.main()
