from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import PeriodicProcessAgent, LoopingProcessAgent
from PyOrchestrate.core.plugins.com import ZeroMQPubSub, SocketType


class Publisher(PeriodicProcessAgent):

    class Config(PeriodicProcessAgent.Config):

        limit = 100
        execution_interval = 0.05
        counter: int = 1

    class Plugin(PeriodicProcessAgent.Plugin):
        zmq = ZeroMQPubSub("tcp://*:5555", SocketType.PUB)

    config: Config
    plugin: Plugin

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

        zmq = ZeroMQPubSub("tcp://localhost:5555", SocketType.SUB)

    plugin: Plugin

    def cycle(self):
        super().cycle()

        message = self.plugin.zmq.recv().decode()
        self.logger.info(f"Received message: {message}")

        if message == "END":
            self.stop()


if __name__ == "__main__":
    orchestrator = Orchestrator(name="CoolOrchestrator")

    # register agents
    orchestrator.register_agent(Publisher, "Publisher")
    orchestrator.register_agent(Subscriber, "Subscriber")

    # start agent
    orchestrator.start()

    # wait for agent to complete
    orchestrator.join()
