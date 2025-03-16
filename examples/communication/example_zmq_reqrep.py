from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import PeriodicProcessAgent, LoopingProcessAgent
from PyOrchestrate.core.plugins.com import ZeroMQReqRep, SocketType
import zmq


class RequestAgent(PeriodicProcessAgent):

    class Config(PeriodicProcessAgent.Config):

        limit = 10
        execution_interval = 0.1
        counter: int = 1

    class Plugin(PeriodicProcessAgent.Plugin):
        zmq = ZeroMQReqRep("tcp://localhost:5555", SocketType.REQ)

    config: Config
    plugin: Plugin

    def runner(self):
        super().runner()

        self.logger.info("Sending message")
        self.plugin.zmq.send(f"Message {self.config.counter}".encode())
        response = self.plugin.zmq.recv()
        self.logger.info(f"Received response: {response.decode()}")
        self.config.counter += 1

    def on_close(self):
        super().on_close()

        self.plugin.zmq.send(b"END")
        response = self.plugin.zmq.recv()
        self.logger.info(f"Received final response: {response.decode()}")


class ReplyAgent(LoopingProcessAgent):

    class Plugin(LoopingProcessAgent.Plugin):

        zmq = ZeroMQReqRep("tcp://localhost:5555", SocketType.REP)

    plugin: Plugin

    def cycle(self):
        super().cycle()

        message = self.plugin.zmq.recv().decode()
        self.logger.info(f"Received message: {message}")

        if message == "END":
            self.plugin.zmq.send(b"OK: END")
            self.stop()
        else:
            self.plugin.zmq.send(b"ACK")


if __name__ == "__main__":
    orchestrator = Orchestrator("CoolOrchestrator")

    # register agents
    orchestrator.register_agent(RequestAgent, "RequestAgent")
    orchestrator.register_agent(ReplyAgent, "ReplyAgent")

    # start agent
    orchestrator.start()

    # wait for agent to complete
    orchestrator.join()
