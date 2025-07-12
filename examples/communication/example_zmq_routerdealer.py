"""
Example demonstrating ZeroMQ Router/Dealer pattern for advanced request/reply routing.

This example shows how to use the ZeroMQRouterDealer class to create an advanced
messaging system where one ROUTER socket can handle multiple DEALER clients.

The Router/Dealer pattern is useful for:
- Load balancing between multiple workers
- Advanced request/reply patterns with client identity tracking
- Asynchronous request/reply messaging
- Building proxy servers and message brokers

Run this script to see multiple dealers communicating with a single router.

Known Issues:
- DEALER identity must currently be set after instantiation instead of in constructor
  This is a temporary limitation that will be addressed in future releases.
"""

import time
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import PeriodicProcessAgent, LoopingProcessAgent
from PyOrchestrate.core.plugins.com import ZeroMQRouterDealer, SocketType


class RouterAgent(LoopingProcessAgent):
    """Agent that acts as a router server, handling multiple dealer clients."""

    class Config(LoopingProcessAgent.Config):
        """Configuration for the RouterAgent."""

        client_count: int = 0  # Track number of connected clients
        max_messages: int = 15  # Stop after processing this many messages

    class Plugin(LoopingProcessAgent.Plugin):
        """Plugin for the RouterAgent."""

        zmq = ZeroMQRouterDealer("tcp://*:5555", SocketType.ROUTER)

    config: Config
    plugin: Plugin

    def cycle(self):
        super().cycle()

        try:
            # Receive message with client identity (non-blocking)
            message_parts = self.plugin.zmq.recv_multipart(blocking=False)
            client_identity = message_parts[0]
            message = message_parts[1].decode()

            self.logger.info(
                f"Router received from {client_identity.decode()}: {message}"
            )

            # Send response back to specific client
            response = f"ACK from Router: {message}"
            self.plugin.zmq.send_multipart([client_identity, response.encode()])

            self.config.client_count += 1

            # Stop after processing enough messages
            if self.config.client_count >= self.config.max_messages:
                self.logger.info("Router processed enough messages, stopping")
                self.stop()

        except Exception as e:
            # No message available, continue
            time.sleep(0.01)


class DealerAgent(PeriodicProcessAgent):
    """Agent that acts as a dealer client, sending requests to the router."""

    class Config(PeriodicProcessAgent.Config):
        """Configuration for the DealerAgent."""

        limit = 5
        execution_interval = 0.5
        counter: int = 1
        dealer_id: str = "dealer1"

    class Plugin(PeriodicProcessAgent.Plugin):
        """Plugin for the DealerAgent."""

        zmq = ZeroMQRouterDealer("tcp://localhost:5555", SocketType.DEALER)

    config: Config
    plugin: Plugin

    def setup(self):
        super().setup()
        # Set dealer identity
        # TODO: This is a known bug - identity should be passed in ZeroMQRouterDealer constructor
        # instead of being set after instantiation. This will be fixed in a future release.
        self.plugin.zmq.identity = (
            self.config.dealer_id.encode()
        )  # BUG: identity must be passed in ZeroMQRouterDealer constructor

    def runner(self):
        super().runner()

        # Send request to router
        message = f"Message {self.config.counter} from {self.config.dealer_id}"
        self.logger.info(f"Dealer {self.config.dealer_id} sending: {message}")
        self.plugin.zmq.send(message.encode())

        # Wait a moment for response
        time.sleep(0.1)

        # Receive response from router
        try:
            response = self.plugin.zmq.recv(blocking=False).decode()
            self.logger.info(f"Dealer {self.config.dealer_id} received: {response}")
        except Exception:
            self.logger.warning(f"Dealer {self.config.dealer_id} no response received")

        self.config.counter += 1

    def on_close(self):
        super().on_close()
        self.logger.info(f"Dealer {self.config.dealer_id} shutting down")


if __name__ == "__main__":
    orchestrator = Orchestrator()

    # Register router agent (server)
    orchestrator.register_agent(RouterAgent, "RouterAgent")

    # Register multiple dealer agents (clients)
    for dealer_id in ["dealer1", "dealer2", "dealer3"]:
        orchestrator.register_agent(
            DealerAgent,
            f"DealerAgent_{dealer_id}",
            custom_config=DealerAgent.Config(
                dealer_id=dealer_id,
                execution_interval=0.3 + (int(dealer_id[-1]) * 0.1),  # Stagger timing
            ),
        )

    # Start all agents
    orchestrator.start()

    # Wait for agents to complete
    orchestrator.join()
