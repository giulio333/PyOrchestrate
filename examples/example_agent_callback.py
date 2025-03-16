import time
import multiprocessing
import requests

from PyOrchestrate.core.orchestrator import Orchestrator, AgentEntry
from PyOrchestrate.core.utilities.event_manager import EventManager
from PyOrchestrate.core.utilities.event import AgentEvent
from PyOrchestrate.core.agent import BaseProcessAgent


class APIFetchAgent(BaseProcessAgent):

    class Config(BaseProcessAgent.Config):
        # URL of the example API (returns JSON data)
        api_url: str = "https://catfact.ninja/fact"
        # Keyword to search in the response
        keyword: str = "and"
        # Polling interval in seconds
        poll_interval: float = 1.0

    config: Config

    def setup(self) -> None:
        """
        Agent initialization: logs the setup.
        """
        super().setup()
        self.logger.info(f"Initializing APIFetchAgent with API: {self.config.api_url}")
        time.sleep(1)

    def execute(self) -> None:
        """
        Polls the external API and, if the keyword is found in the data,
        logs a warning.
        """
        super().execute()
        self.logger.info(
            f"Starting API polling every {self.config.poll_interval} seconds for keyword: '{self.config.keyword}'"
        )
        try:
            # For example, perform 5 requests
            for _ in range(5):
                self.logger.info("Requesting data from the external API...")
                response = requests.get(self.config.api_url)
                if response.status_code == 200:
                    json_data = response.json()
                    # Construct a string with some useful information
                    message_str = f"Body: {json_data.get('fact', '')}"
                    self.logger.info("Data received")
                    # Check if the keyword is present in the string
                    if self.config.keyword in message_str:
                        self.logger.warning(f"Keyword '{self.config.keyword}' found!")
                        # Qui eventualmente si potrebbe usare l'EventManager per emettere un evento
                    else:
                        self.logger.info("Keyword not found in this cycle.")
                else:
                    self.logger.error(
                        f"Error accessing API: status code {response.status_code}"
                    )
                time.sleep(self.config.poll_interval)
        except Exception as e:
            self.logger.exception(f"Error during API polling: {e}")
        finally:
            # In questo esempio semplificato non è necessaria una comunicazione esterna
            pass

    def on_stop(self):
        """
        Logs the termination of the agent.
        """
        self.logger.info("APIFetchAgent terminated.")


def on_agent_start(event_date, event_time):
    message = f"Agent start. Date: {event_date}, Time: {event_time}"
    print(message)


def on_agent_close(event_date, event_time):
    message = f"Agent stop. Date: {event_date}, Time: {event_time}"
    print(message)


if __name__ == "__main__":
    # Required for multiprocessing support
    multiprocessing.set_start_method("spawn")

    # Orchestrator initialization
    orchestrator = Orchestrator()

    # Create an EventManager
    event_manager = EventManager()
    event_manager.connect(AgentEvent.AGENT_START, on_agent_start)
    event_manager.connect(AgentEvent.AGENT_CLOSE, on_agent_close)

    # Registering agents (solo APIFetchAgent è registrato)
    fetch_agent: AgentEntry = orchestrator.register_agent(
        APIFetchAgent, "APIFetchAgent", event_manager=event_manager
    )

    # Starting agents
    orchestrator.start()

    # Waiting for agents to terminate
    orchestrator.join()
