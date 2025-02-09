from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import PeriodicProcessAgent, LoopingProcessAgent
from PyOrchestrate.core.plugins.com import ZeroMQPubSub
import zmq


class PubConfig(PeriodicProcessAgent.Config):

    limit = 100
    execution_interval = 0.01
    zmq = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
    counter: int = 1


class Publisher(PeriodicProcessAgent[PubConfig]):

    Config = PubConfig

    def setup(self):
        """
        Setup method for the agent.
        """
        super().setup()

        self.config.zmq.initialize()

    def runner(self):
        """
        Runner method for the agent.
        """
        super().runner()

        self.logger.info("Sending message")
        self.config.zmq.send(f"Message {self.config.counter}".encode())
        self.config.counter += 1

    def on_close(self):
        super().on_close()

        self.config.zmq.send(b"END")
        self.config.zmq.finalize()


class SubConfig(LoopingProcessAgent.Config):

    zmq = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB)


class Subscriber(LoopingProcessAgent[SubConfig]):

    Config = SubConfig

    def setup(self):
        super().setup()

        self.config.zmq.initialize()

    def cycle(self):
        super().cycle()

        message = self.config.zmq.recv().decode()
        self.logger.info(f"Received message: {message}")

        if message == "END":
            self.stop()

    def on_close(self):
        super().on_close()

        self.config.zmq.finalize()


if __name__ == "__main__":
    orchestrator = Orchestrator("CoolOrchestrator")

    # register agents
    orchestrator.register_agent(Publisher, "Publisher")
    orchestrator.register_agent(Subscriber, "Subscriber")

    # start agent
    orchestrator.start()

    # wait for agent to complete
    orchestrator.join()
