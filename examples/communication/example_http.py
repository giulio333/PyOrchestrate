from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import PeriodicProcessAgent, LoopingProcessAgent
from PyOrchestrate.core.plugins.com import HTTPPlugin
import requests


class HTTPRequestAgent(PeriodicProcessAgent):

    class Config(PeriodicProcessAgent.Config):

        limit = 10
        execution_interval = 5
        counter: int = 1

    class Plugin(PeriodicProcessAgent.Plugin):
        http = HTTPPlugin("http://localhost:8000")

    config: Config
    plugin: Plugin

    def runner(self):
        super().runner()

        self.logger.info("Sending HTTP request")
        response = self.plugin.http.send(f"Message {self.config.counter}")
        self.logger.info(f"Received response: {response.text}")
        self.config.counter += 1

    def on_close(self):
        super().on_close()

        self.plugin.http.finalize()


class HTTPResponseAgent(LoopingProcessAgent):

    class Plugin(LoopingProcessAgent.Plugin):

        http = HTTPPlugin("http://localhost:8000")

    plugin: Plugin

    def cycle(self):
        super().cycle()

        response = self.plugin.http.recv()
        self.logger.info(f"Received message: {response}")

        if response == "END":
            self.stop()


if __name__ == "__main__":
    orchestrator = Orchestrator("HTTPOrchestrator")

    # register agents
    orchestrator.register_agent(HTTPRequestAgent, "HTTPRequestAgent")
    orchestrator.register_agent(HTTPResponseAgent, "HTTPResponseAgent")

    # start agent
    orchestrator.start()

    # wait for agent to complete
    orchestrator.join()
