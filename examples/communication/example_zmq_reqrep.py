from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import PeriodicProcessAgent, LoopingProcessAgent
from PyOrchestrate.core.plugins.com import ZeroMQReqRep
import zmq


class ReqConfig(PeriodicProcessAgent.Config):

    limit = 10
    execution_interval = 0.1
    zmq = ZeroMQReqRep("tcp://localhost:5555", zmq.REQ)
    counter: int = 1


class RequestAgent(PeriodicProcessAgent[ReqConfig]):

    Config = ReqConfig

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
        response = self.config.zmq.recv()
        self.logger.info(f"Received response: {response.decode()}")
        self.config.counter += 1

    def on_close(self):
        super().on_close()

        self.config.zmq.send(b"END")
        response = self.config.zmq.recv()
        self.logger.info(f"Received final response: {response.decode()}")
        self.config.zmq.finalize()


class RepConfig(LoopingProcessAgent.Config):

    zmq = ZeroMQReqRep("tcp://localhost:5555", zmq.REP)


class ReplyAgent(LoopingProcessAgent[RepConfig]):

    Config = RepConfig

    def setup(self):
        super().setup()

        self.config.zmq.initialize()

    def cycle(self):
        super().cycle()

        message = self.config.zmq.recv().decode()
        self.logger.info(f"Received message: {message}")

        if message == "END":
            self.config.zmq.send(b"OK: END")
            self.stop()
        else:
            self.config.zmq.send(b"ACK")

    def on_close(self):
        super().on_close()

        self.config.zmq.finalize()


if __name__ == "__main__":
    orchestrator = Orchestrator("CoolOrchestrator")

    # register agents
    orchestrator.register_agent(RequestAgent, "RequestAgent")
    orchestrator.register_agent(ReplyAgent, "ReplyAgent")

    # start agent
    orchestrator.start()

    # wait for agent to complete
    orchestrator.join()
