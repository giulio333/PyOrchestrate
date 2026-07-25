import unittest
import zmq
import time
from PyOrchestrate.core.plugins.com import (
    ZeroMQPubSub,
    ZeroMQReqRep,
    ZeroMQPushPull,
    ZeroMQRouterDealer,
    ZeroMQPair,
    ZeroMQPoller,
    SocketType,
)


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


class TestZeroMQRouterDealer(unittest.TestCase):

    def test_invalid_socket_type(self):
        # Only SocketType.ROUTER and SocketType.DEALER are supported.
        with self.assertRaises(ValueError):
            plugin = ZeroMQRouterDealer("tcp://127.0.0.1:5558", SocketType.PUB)
            plugin.initialize()

    def test_router_dealer_communication(self):
        address = "tcp://127.0.0.1:5558"

        # Initialize the ROUTER first (server)
        router = ZeroMQRouterDealer(address, SocketType.ROUTER)
        router.initialize()

        # Initialize the DEALER (client)
        dealer = ZeroMQRouterDealer(address, SocketType.DEALER, identity=b"client1")
        dealer.initialize()

        # Allow connection to establish
        time.sleep(0.1)

        # Send message from DEALER to ROUTER
        test_message = b"Hello from DEALER"
        dealer.send(test_message)

        # Receive on ROUTER (should include client identity)
        time.sleep(0.1)
        message_parts = router.recv_multipart()
        self.assertEqual(len(message_parts), 2)
        client_identity = message_parts[0]
        received_message = message_parts[1]
        self.assertEqual(received_message, test_message)

        # Send reply from ROUTER to DEALER
        reply_message = b"Hello from ROUTER"
        router.send_multipart([client_identity, reply_message])

        # Receive reply on DEALER
        time.sleep(0.1)
        received_reply = dealer.recv()
        self.assertEqual(received_reply, reply_message)

        # Finalize both plugins
        router.finalize()
        dealer.finalize()

    def test_non_blocking_operations(self):
        address = "tcp://127.0.0.1:5559"

        router = ZeroMQRouterDealer(address, SocketType.ROUTER)
        router.initialize()

        dealer = ZeroMQRouterDealer(address, SocketType.DEALER)
        dealer.initialize()

        time.sleep(0.1)

        # Test non-blocking send
        dealer.send(b"test", blocking=False)

        # Test non-blocking receive with no message available
        with self.assertRaises(zmq.error.Again):
            dealer.recv(blocking=False)

        router.finalize()
        dealer.finalize()


class TestZeroMQPair(unittest.TestCase):

    def test_pair_communication(self):
        address = "tcp://127.0.0.1:5560"

        # Initialize first PAIR socket (bind)
        pair_a = ZeroMQPair(address, bind=True)
        pair_a.initialize()

        # Initialize second PAIR socket (connect)
        pair_b = ZeroMQPair(address, bind=False)
        pair_b.initialize()

        # Allow connection to establish
        time.sleep(0.1)

        # Test bidirectional communication
        message_a = b"Hello from A"
        pair_a.send(message_a)
        time.sleep(0.1)
        received_by_b = pair_b.recv()
        self.assertEqual(received_by_b, message_a)

        message_b = b"Hello from B"
        pair_b.send(message_b)
        time.sleep(0.1)
        received_by_a = pair_a.recv()
        self.assertEqual(received_by_a, message_b)

        # Finalize both plugins
        pair_a.finalize()
        pair_b.finalize()

    def test_non_blocking_operations(self):
        address = "tcp://127.0.0.1:5561"

        pair_a = ZeroMQPair(address, bind=True)
        pair_a.initialize()

        pair_b = ZeroMQPair(address, bind=False)
        pair_b.initialize()

        time.sleep(0.1)

        # Test non-blocking send
        pair_a.send(b"test", blocking=False)

        # Test non-blocking receive with no message available
        with self.assertRaises(zmq.error.Again):
            pair_a.recv(blocking=False)

        pair_a.finalize()
        pair_b.finalize()


class TestZeroMQPoller(unittest.TestCase):

    def test_poller_basic_functionality(self):
        address = "tcp://127.0.0.1:5562"

        # Create PUB/SUB sockets
        pub = ZeroMQPubSub(address, SocketType.PUB)
        sub = ZeroMQPubSub(address, SocketType.SUB, subscribe_topic=b"")

        pub.initialize()
        sub.initialize()

        # Create poller
        poller = ZeroMQPoller()
        poller.initialize()

        # Register SUB socket for reading
        poller.register(sub.socket, zmq.POLLIN)

        # Allow connection to establish
        time.sleep(0.1)

        # Poll with timeout (should return empty list)
        events = poller.poll(timeout=100)  # 100ms timeout
        self.assertEqual(len(events), 0)

        # Send a message
        pub.send(b"test message")
        time.sleep(0.1)

        # Poll again (should now have an event)
        events = poller.poll(timeout=100)
        self.assertEqual(len(events), 1)
        socket, event = events[0]
        self.assertEqual(socket, sub.socket)
        self.assertTrue(event & zmq.POLLIN)

        # Read the message
        message = sub.recv()
        self.assertEqual(message, b"test message")

        # Finalize everything
        poller.finalize()
        pub.finalize()
        sub.finalize()

    def test_poller_unregister(self):
        address = "tcp://127.0.0.1:5563"

        pub = ZeroMQPubSub(address, SocketType.PUB)
        sub = ZeroMQPubSub(address, SocketType.SUB, subscribe_topic=b"")

        pub.initialize()
        sub.initialize()

        poller = ZeroMQPoller()
        poller.initialize()

        # Register and then unregister
        poller.register(sub.socket, zmq.POLLIN)
        poller.unregister(sub.socket)

        time.sleep(0.1)

        # Send message
        pub.send(b"test message")
        time.sleep(0.1)

        # Poll should return empty since socket is unregistered
        events = poller.poll(timeout=100)
        self.assertEqual(len(events), 0)

        poller.finalize()
        pub.finalize()
        sub.finalize()


class TestEnhancedNonBlockingOperations(unittest.TestCase):

    def test_pubsub_non_blocking(self):
        address = "tcp://127.0.0.1:5564"

        pub = ZeroMQPubSub(address, SocketType.PUB)
        sub = ZeroMQPubSub(address, SocketType.SUB, subscribe_topic=b"")

        pub.initialize()
        sub.initialize()

        time.sleep(0.1)

        # Test non-blocking receive with no message available.
        # Asserted BEFORE sending anything: checking it after a send would be a
        # race against delivery, not a test of the non-blocking behaviour.
        with self.assertRaises(zmq.error.Again):
            sub.recv(blocking=False)

        # Test non-blocking send. Delivery is deliberately not asserted here:
        # PUB drops messages for subscribers whose subscription has not
        # propagated yet, so any such assertion would be flaky by design.
        pub.send(b"test", blocking=False)

        pub.finalize()
        sub.finalize()

    def test_reqrep_non_blocking(self):
        address = "tcp://127.0.0.1:5565"

        rep = ZeroMQReqRep(address, SocketType.REP)
        req = ZeroMQReqRep(address, SocketType.REQ)

        rep.initialize()
        req.initialize()

        time.sleep(0.1)

        # Test non-blocking send
        req.send(b"test", blocking=False)

        # Test non-blocking receive with no message available
        with self.assertRaises(zmq.error.Again):
            req.recv(blocking=False)

        rep.finalize()
        req.finalize()

    def test_pushpull_non_blocking(self):
        address = "tcp://127.0.0.1:5566"

        push = ZeroMQPushPull(address, SocketType.PUSH)
        pull = ZeroMQPushPull(address, SocketType.PULL)

        push.initialize()
        pull.initialize()

        # Let the PULL connection register: a PUSH with no connected peer
        # raises Again on a non-blocking send, which is not what is tested here.
        time.sleep(0.1)

        # Test non-blocking receive with no message available.
        # Asserted BEFORE sending anything. Doing it after a send raced the
        # delivery: PUSH/PULL queues reliably, so the message does arrive and
        # whether it had arrived yet depended on timing.
        with self.assertRaises(zmq.error.Again):
            pull.recv(blocking=False)

        # Test non-blocking send
        push.send(b"test", blocking=False)

        # The message is queued, so it does arrive: wait for it instead of
        # asserting on an arbitrary sleep.
        self.assertTrue(pull.socket.poll(timeout=5000), "message never arrived")
        self.assertEqual(pull.recv(blocking=False), b"test")

        push.finalize()
        pull.finalize()


if __name__ == "__main__":
    unittest.main()
