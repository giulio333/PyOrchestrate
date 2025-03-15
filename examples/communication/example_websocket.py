from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import PeriodicProcessAgent, LoopingProcessAgent
from PyOrchestrate.core.plugins.com import WebSocketPlugin
import websocket


class WebSocketSendAgent(PeriodicProcessAgent):

    class Config(PeriodicProcessAgent.Config):

        limit = 10
        execution_interval = 5
        counter: int = 1

    class Plugin(PeriodicProcessAgent.Plugin):
        ws = WebSocketPlugin("ws://localhost:8000")

    config: Config
    plugin: Plugin

    def runner(self):
        super().runner()

        self.logger.info("Sending WebSocket message")
        self.plugin.ws.send(f"Message {self.config.counter}")
        self.config.counter += 1

    def on_close(self):
        super().on_close()

        self.plugin.ws.finalize()


class WebSocketReceiveAgent(LoopingProcessAgent):

    class Plugin(LoopingProcessAgent.Plugin):

        ws = WebSocketPlugin("ws://localhost:8000")

    plugin: Plugin

    def cycle(self):
        super().cycle()

        message = self.plugin.ws.recv()
        self.logger.info(f"Received message: {message}")

        if message == "END":
            self.stop()


if __name__ == "__main__":
    orchestrator = Orchestrator("WebSocketOrchestrator")

    # register agents
    orchestrator.register_agent(WebSocketSendAgent, "WebSocketSendAgent")
    orchestrator.register_agent(WebSocketReceiveAgent, "WebSocketReceiveAgent")

    # start agent
    orchestrator.start()

    # wait for agent to complete
    orchestrator.join()
