import time
import multiprocessing
import requests
import zmq

from PyOrchestrate.core.orchestrator import Orchestrator, AgentEntry
from PyOrchestrate.core.agent import PeriodicProcessAgent
from PyOrchestrate.core.plugins import ZeroMQPubSub


class APIFetchAgent(PeriodicProcessAgent):

    class Config(PeriodicProcessAgent.Config):
        api_url: str = "https://catfact.ninja/fact"
        """Url of the external API to fetch data from."""
        keyword: str = "and"
        """Keyword to search for in the fetched data."""

    config: Config

    def setup(self) -> None:
        """
        Agent initialization: registers the communication plugin and logs the setup.
        """
        super().setup()
        self.socket = ZeroMQPubSub("tcp://localhost:5555", zmq.PUB).initialize()
        time.sleep(1)

    def _fetch_data(self):
        """
        Fetches data from the external API.
        """
        self.logger.info("Requesting data from the external API...")
        response = requests.get(self.config.api_url)
        if response.status_code == 200:
            return response.json()

        self.logger.error(f"Error accessing API: status code {response.status_code}")
        return None

    def _handle_api_response(self, json_data: dict):
        """
        Handles the data received from the external API and checks for the keyword.
        """
        message_str = f"Body: {json_data.get('fact', '')}"
        self.logger.info("Data received from API:")
        self.logger.info(message_str)
        if self.config.keyword in message_str:
            self.logger.warning(f"Keyword '{self.config.keyword}' found!")

            return message_str

    def runner(self) -> None:
        """
        Polls the external API and, if the keyword is found in the data,
        sends a message to the other agent.
        """
        super().runner()

        json_data = self._fetch_data()

        if json_data:
            message = self._handle_api_response(json_data)
            if message:
                self.socket.send(message.encode())

    def on_close(self):
        """
        Logs the termination of the agent.
        """
        self.logger.info("APIFetchAgent terminated.")
        self.socket.send("STOP".encode())
        self.socket.finalize()


class APIAlertAgent(PeriodicProcessAgent):
    class Config(PeriodicProcessAgent.Config):
        api_url: str = "https://catfact.ninja/fact"
        """Url of the external API to fetch data from."""
        keyword: str = "and"
        """Keyword to search for in the fetched data."""

    config: Config

    def setup(self) -> None:
        """
        Initializes the agent for receiving messages.
        """
        super().setup()
        self.socket = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB).initialize()

    def runner(self) -> None:
        """
        Listens for messages sent by APIFetchAgent.
        """
        super().runner()

        message: str = self.socket.recv().decode()

        self.logger.success(f"Message received: {message}")

        if message == "STOP":
            self.logger.warning("Received STOP signal.")
            self.stop()

    def on_close(self):
        """
        Logs the termination of the agent.
        """
        self.logger.info("APIAlertAgent terminated.")
        self.socket.finalize()


if __name__ == "__main__":
    # Required for multiprocessing support
    multiprocessing.set_start_method("spawn")

    # Orchestrator initialization
    orchestrator = Orchestrator()

    # Registering agents
    fetch_agent: AgentEntry = orchestrator.register_agent(
        APIFetchAgent,
        "APIFetchAgent",
        APIAlertAgent.Config(execution_interval=1, limit=5),
    )
    alert_agent: AgentEntry = orchestrator.register_agent(
        APIAlertAgent, "APIAlertAgent", APIAlertAgent.Config(execution_interval=1)
    )

    # Starting agents
    orchestrator.start()

    # Waiting for agents to terminate
    orchestrator.join()
