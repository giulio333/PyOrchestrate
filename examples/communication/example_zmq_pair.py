"""
Example demonstrating ZeroMQ Pair pattern for bidirectional exclusive connections.

This example shows how to use the ZeroMQPair class to create exclusive
bidirectional communication between two peers.

The Pair pattern is useful for:
- Direct peer-to-peer communication
- Bidirectional data exchange
- Exclusive connections between two endpoints
- Simple inter-process communication

Run this script to see two pairs communicating bidirectionally.
"""

import time
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import PeriodicProcessAgent
from PyOrchestrate.core.plugins.com import ZeroMQPair


class PairAgentA(PeriodicProcessAgent):
    """Agent that acts as the first peer in a PAIR connection."""

    class Config(PeriodicProcessAgent.Config):
        """Configuration for PairAgentA."""

        limit = 10
        execution_interval = 1.0
        counter: int = 1

    class Plugin(PeriodicProcessAgent.Plugin):
        """Plugin for PairAgentA."""

        zmq = ZeroMQPair("tcp://*:5555", bind=True)  # This peer binds

    config: Config
    plugin: Plugin

    def runner(self):
        super().runner()

        # Send message to peer B
        message = f"Hello from A - Message {self.config.counter}"
        self.logger.info(f"Peer A sending: {message}")
        self.plugin.zmq.send(message.encode())

        # Try to receive response from peer B
        try:
            time.sleep(0.1)  # Small delay to allow response
            response = self.plugin.zmq.recv(blocking=False).decode()
            self.logger.info(f"Peer A received: {response}")
        except Exception:
            self.logger.debug("Peer A: No response received yet")

        self.config.counter += 1

    def on_close(self):
        super().on_close()
        self.logger.info("Peer A shutting down")


class PairAgentB(PeriodicProcessAgent):
    """Agent that acts as the second peer in a PAIR connection."""

    class Config(PeriodicProcessAgent.Config):
        """Configuration for PairAgentB."""

        limit = 10
        execution_interval = 1.2  # Slightly different timing
        counter: int = 1

    class Plugin(PeriodicProcessAgent.Plugin):
        """Plugin for PairAgentB."""

        zmq = ZeroMQPair("tcp://localhost:5555", bind=False)  # This peer connects

    config: Config
    plugin: Plugin

    def runner(self):
        super().runner()

        # Try to receive message from peer A
        try:
            message = self.plugin.zmq.recv(blocking=False).decode()
            self.logger.info(f"Peer B received: {message}")

            # Send response to peer A
            response = f"Response from B - Counter {self.config.counter}"
            self.logger.info(f"Peer B sending: {response}")
            self.plugin.zmq.send(response.encode())

        except Exception:
            # No message available, send our own message
            message = f"Hello from B - Message {self.config.counter}"
            self.logger.info(f"Peer B sending: {message}")
            self.plugin.zmq.send(message.encode())

        self.config.counter += 1

    def on_close(self):
        super().on_close()
        self.logger.info("Peer B shutting down")


class PairAgentListener(PeriodicProcessAgent):
    """A listener agent that only receives messages without sending."""

    class Config(PeriodicProcessAgent.Config):
        """Configuration for PairAgentListener."""

        limit = 20  # Listen for more messages
        execution_interval = 0.5

    class Plugin(PeriodicProcessAgent.Plugin):
        """Plugin for PairAgentListener."""

        zmq = ZeroMQPair("tcp://*:5556", bind=True)  # Different port

    config: Config
    plugin: Plugin

    def runner(self):
        super().runner()

        # Just listen for messages
        try:
            message = self.plugin.zmq.recv(blocking=False).decode()
            self.logger.info(f"Listener received: {message}")
        except Exception:
            self.logger.debug("Listener: No message received")


class PairAgentSender(PeriodicProcessAgent):
    """A sender agent that sends messages to the listener."""

    class Config(PeriodicProcessAgent.Config):
        """Configuration for PairAgentSender."""

        limit = 8
        execution_interval = 1.5
        counter: int = 1

    class Plugin(PeriodicProcessAgent.Plugin):
        """Plugin for PairAgentSender."""

        zmq = ZeroMQPair("tcp://localhost:5556", bind=False)

    config: Config
    plugin: Plugin

    def runner(self):
        super().runner()

        # Send message to listener
        message = f"Broadcast message {self.config.counter} from Sender"
        self.logger.info(f"Sender sending: {message}")
        self.plugin.zmq.send(message.encode())

        self.config.counter += 1

    def on_close(self):
        super().on_close()
        self.logger.info("Sender shutting down")


if __name__ == "__main__":
    orchestrator = Orchestrator()

    # Register bidirectional pair agents
    orchestrator.register_agent(PairAgentA, "PairAgentA")
    orchestrator.register_agent(PairAgentB, "PairAgentB")

    # Register unidirectional pair agents
    orchestrator.register_agent(PairAgentListener, "PairAgentListener")
    orchestrator.register_agent(PairAgentSender, "PairAgentSender")

    # Start all agents
    orchestrator.start()

    # Wait for agents to complete
    orchestrator.join()
