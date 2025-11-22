"""
Example demonstrating the simplified plugin instantiation pattern.

This example shows how the improved BaseClassPlugin eliminates the need
for explicit __init__ implementations when defining custom Plugin classes.
"""

from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import PeriodicProcessAgent
from PyOrchestrate.core.plugins.com import ZeroMQPubSub, SocketType


class Publisher(PeriodicProcessAgent):
    """
    Publisher agent demonstrating the simplified plugin pattern.

    Notice how the Plugin class doesn't need an __init__ method!
    Plugins are simply defined as class attributes and can be
    overridden via constructor if needed.
    """

    class Config(PeriodicProcessAgent.Config):
        limit = 10
        execution_interval = 1.0

    class Plugin(PeriodicProcessAgent.Plugin):
        # Simply define plugins as class attributes - no __init__ needed!
        zmq = ZeroMQPubSub("tcp://*:5557", SocketType.PUB)

    config: Config
    plugin: Plugin

    def runner(self):
        super().runner()
        message = f"Hello from Publisher"
        self.logger.info(f"Publishing: {message}")
        self.plugin.zmq.send(message.encode())


class Subscriber(PeriodicProcessAgent):
    """
    Subscriber agent demonstrating the simplified plugin pattern.
    """

    class Config(PeriodicProcessAgent.Config):
        limit = 10
        execution_interval = 0.5

    class Plugin(PeriodicProcessAgent.Plugin):
        # Again, no __init__ needed - just define the plugin!
        zmq = ZeroMQPubSub("tcp://localhost:5557", SocketType.SUB)

    config: Config
    plugin: Plugin

    def runner(self):
        super().runner()
        try:
            message = self.plugin.zmq.recv(blocking=False).decode()
            self.logger.info(f"Received: {message}")
        except Exception:
            # No message available
            pass


if __name__ == "__main__":
    print("=" * 70)
    print("Simplified Plugin Pattern Example")
    print("=" * 70)
    print()
    print("Key improvements:")
    print("1. No explicit __init__ needed in Plugin classes")
    print("2. Plugins defined as simple class attributes")
    print("3. Can still override via constructor if needed")
    print("4. Cleaner, more maintainable code")
    print()
    print("Starting orchestrator...")
    print("=" * 70)
    print()

    orchestrator = Orchestrator()

    # Register agents with default plugin configurations
    orchestrator.register_agent(Publisher, "Publisher")
    orchestrator.register_agent(Subscriber, "Subscriber")

    # You could also override plugins at registration time:
    # custom_plugin = ZeroMQPubSub("tcp://*:5558", SocketType.PUB)
    # orchestrator.register_agent(
    #     Publisher,
    #     "CustomPublisher",
    #     custom_config=Publisher.Config(),
    #     custom_plugin=Publisher.Plugin(zmq=custom_plugin)
    # )

    orchestrator.start()
    orchestrator.join()

    print()
    print("=" * 70)
    print("Example completed successfully!")
    print("=" * 70)
