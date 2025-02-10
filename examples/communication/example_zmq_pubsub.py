from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import PeriodicProcessAgent, LoopingProcessAgent
from PyOrchestrate.core.plugins.com import ZeroMQPubSub
import zmq


class Publisher(PeriodicProcessAgent):

    class Config(PeriodicProcessAgent.Config):

        limit = 10
        execution_interval = 0.1
        counter: int = 1

    class Plugin(PeriodicProcessAgent.Plugin):
        zmq = ZeroMQPubSub("tcp://*:5555", zmq.PUB)

    def setup(self):
        super().setup()

        self.plugin: Subscriber.Plugin

    def runner(self):
        super().runner()

        self.logger.info("Sending message")
        self.plugin.zmq.send(f"Message {self.config.counter}".encode())
        self.config.counter += 1

    def on_close(self):
        super().on_close()

        self.plugin.zmq.send(b"END")


class Subscriber(LoopingProcessAgent):

    class Plugin(LoopingProcessAgent.Plugin):

        zmq = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB)

    def setup(self):
        super().setup()

        self.plugin: Subscriber.Plugin

    def cycle(self):
        super().cycle()

        message = self.plugin.zmq.recv().decode()
        self.logger.info(f"Received message: {message}")

        if message == "END":
            self.stop()

    def on_close(self):
        super().on_close()


if __name__ == "__main__":
    orchestrator = Orchestrator("CoolOrchestrator")

    # register agents
    orchestrator.register_agent(Publisher, "Publisher")
    orchestrator.register_agent(Subscriber, "Subscriber")

    # start agent
    orchestrator.start()

    # wait for agent to complete
    orchestrator.join()
