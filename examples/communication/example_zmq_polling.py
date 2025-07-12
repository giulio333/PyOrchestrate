"""
Example demonstrating ZeroMQ Poller for non-blocking event-driven communication.

This example shows how to use the ZeroMQPoller class to handle multiple
sockets in an event-driven manner, avoiding blocking operations.

The Poller is useful for:
- Non-blocking operations across multiple sockets
- Event-driven programming
- Handling multiple communication patterns simultaneously
- Building reactive systems

Run this script to see polling in action with multiple socket types.
"""

import time
import zmq
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import LoopingProcessAgent
from PyOrchestrate.core.plugins.com import (
    ZeroMQPubSub, ZeroMQReqRep, ZeroMQPair, ZeroMQPoller, SocketType
)


class PollingAgent(LoopingProcessAgent):
    """Agent that uses polling to handle multiple socket types."""

    class Config(LoopingProcessAgent.Config):
        """Configuration for the PollingAgent."""
        
        message_count: int = 0
        max_messages: int = 20

    class Plugin(LoopingProcessAgent.Plugin):
        """Plugin for the PollingAgent."""
        
        # Multiple communication patterns
        sub_socket = ZeroMQPubSub("tcp://localhost:5555", SocketType.SUB, subscribe_topic=b"")
        rep_socket = ZeroMQReqRep("tcp://*:5556", SocketType.REP)
        pair_socket = ZeroMQPair("tcp://*:5557", bind=True)
        poller = ZeroMQPoller()

    config: Config
    plugin: Plugin

    def setup(self):
        super().setup()
        
        # Initialize all sockets
        self.plugin.sub_socket.initialize()
        self.plugin.rep_socket.initialize()
        self.plugin.pair_socket.initialize()
        self.plugin.poller.initialize()
        
        # Register sockets with poller
        self.plugin.poller.register(self.plugin.sub_socket.socket, zmq.POLLIN)
        self.plugin.poller.register(self.plugin.rep_socket.socket, zmq.POLLIN)
        self.plugin.poller.register(self.plugin.pair_socket.socket, zmq.POLLIN)

    def cycle(self):
        super().cycle()

        # Poll for events with a timeout
        events = self.plugin.poller.poll(timeout=100)  # 100ms timeout
        
        if not events:
            self.logger.debug("No events received")
            return

        # Process events
        for socket, event in events:
            if event & zmq.POLLIN:
                self.handle_incoming_message(socket)
            if event & zmq.POLLOUT:
                self.logger.debug("Socket ready for writing")

        # Stop after processing enough messages
        if self.config.message_count >= self.config.max_messages:
            self.logger.info("Processed enough messages, stopping")
            self.stop()

    def handle_incoming_message(self, socket):
        """Handle incoming messages based on socket type."""
        try:
            if socket == self.plugin.sub_socket.socket:
                message = self.plugin.sub_socket.recv(blocking=False)
                self.logger.info(f"SUB received: {message.decode()}")
                
            elif socket == self.plugin.rep_socket.socket:
                request = self.plugin.rep_socket.recv(blocking=False)
                self.logger.info(f"REP received: {request.decode()}")
                
                # Send reply
                reply = f"ACK: {request.decode()}"
                self.plugin.rep_socket.send(reply.encode(), blocking=False)
                
            elif socket == self.plugin.pair_socket.socket:
                message = self.plugin.pair_socket.recv(blocking=False)
                self.logger.info(f"PAIR received: {message.decode()}")
                
                # Send response
                response = f"Echo: {message.decode()}"
                self.plugin.pair_socket.send(response.encode(), blocking=False)
                
            self.config.message_count += 1
            
        except zmq.error.Again:
            # No message available (shouldn't happen since we polled)
            self.logger.debug("No message available despite poll event")
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")


class PublisherAgent(LoopingProcessAgent):
    """Agent that publishes messages to the SUB socket."""

    class Config(LoopingProcessAgent.Config):
        """Configuration for the PublisherAgent."""
        
        counter: int = 1
        max_messages: int = 8

    class Plugin(LoopingProcessAgent.Plugin):
        """Plugin for the PublisherAgent."""
        
        zmq = ZeroMQPubSub("tcp://*:5555", SocketType.PUB)

    config: Config
    plugin: Plugin

    def cycle(self):
        super().cycle()

        if self.config.counter > self.config.max_messages:
            self.stop()
            return

        # Publish message
        message = f"Published message {self.config.counter}"
        self.logger.info(f"Publishing: {message}")
        self.plugin.zmq.send(message.encode())
        
        self.config.counter += 1
        time.sleep(1)  # Publish every second


class RequesterAgent(LoopingProcessAgent):
    """Agent that sends requests to the REP socket."""

    class Config(LoopingProcessAgent.Config):
        """Configuration for the RequesterAgent."""
        
        counter: int = 1
        max_messages: int = 6

    class Plugin(LoopingProcessAgent.Plugin):
        """Plugin for the RequesterAgent."""
        
        zmq = ZeroMQReqRep("tcp://localhost:5556", SocketType.REQ)

    config: Config
    plugin: Plugin

    def cycle(self):
        super().cycle()

        if self.config.counter > self.config.max_messages:
            self.stop()
            return

        # Send request
        request = f"Request {self.config.counter}"
        self.logger.info(f"Sending request: {request}")
        self.plugin.zmq.send(request.encode())
        
        # Receive reply
        try:
            reply = self.plugin.zmq.recv(blocking=False)
            self.logger.info(f"Received reply: {reply.decode()}")
        except zmq.error.Again:
            self.logger.warning("No reply received")
        
        self.config.counter += 1
        time.sleep(1.5)  # Send requests every 1.5 seconds


class PairCommunicatorAgent(LoopingProcessAgent):
    """Agent that communicates with the PAIR socket."""

    class Config(LoopingProcessAgent.Config):
        """Configuration for the PairCommunicatorAgent."""
        
        counter: int = 1
        max_messages: int = 5

    class Plugin(LoopingProcessAgent.Plugin):
        """Plugin for the PairCommunicatorAgent."""
        
        zmq = ZeroMQPair("tcp://localhost:5557", bind=False)

    config: Config
    plugin: Plugin

    def cycle(self):
        super().cycle()

        if self.config.counter > self.config.max_messages:
            self.stop()
            return

        # Send message to pair
        message = f"Pair message {self.config.counter}"
        self.logger.info(f"Sending to pair: {message}")
        self.plugin.zmq.send(message.encode())
        
        # Receive response
        try:
            time.sleep(0.1)  # Small delay for response
            response = self.plugin.zmq.recv(blocking=False)
            self.logger.info(f"Received from pair: {response.decode()}")
        except zmq.error.Again:
            self.logger.debug("No response from pair")
        
        self.config.counter += 1
        time.sleep(2)  # Send every 2 seconds


if __name__ == "__main__":
    orchestrator = Orchestrator()

    # Register the polling agent (central receiver)
    orchestrator.register_agent(PollingAgent, "PollingAgent")

    # Register sender agents
    orchestrator.register_agent(PublisherAgent, "PublisherAgent")
    orchestrator.register_agent(RequesterAgent, "RequesterAgent")
    orchestrator.register_agent(PairCommunicatorAgent, "PairCommunicatorAgent")

    # Start all agents
    orchestrator.start()

    # Wait for agents to complete
    orchestrator.join()