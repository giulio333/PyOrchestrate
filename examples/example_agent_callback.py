import time
import requests

from PyOrchestrate.core.orchestrator import Orchestrator, AgentEntry
from PyOrchestrate.core.utilities.event import OrchestratorEvent
from PyOrchestrate.core.agent import BaseProcessAgent

from PyOrchestrate.core.base.utilities import LoggerConfig


class APIFetchAgent(BaseProcessAgent):

    class Config(BaseProcessAgent.Config):
        # URL of the example API (returns JSON data)
        api_url: str = "https://catfact.ninja/fact"
        # Keyword to search in the response
        keyword: str = "and"
        # Polling interval in seconds
        poll_interval: float = 1.0

        logger_config = LoggerConfig("TRACE")

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
                    else:
                        self.logger.info("Keyword not found in this cycle.")
                else:
                    self.logger.error(
                        f"Error accessing API: status code {response.status_code}"
                    )
                time.sleep(self.config.poll_interval)
        except Exception as e:
            self.logger.exception(f"Error during API polling: {e}")

    def on_stop(self):
        """
        Logs the termination of the agent.
        """
        super().on_stop()
        self.logger.info("APIFetchAgent terminated.")


def on_agent_start(agent_name, **kwargs):
    """
    Callback function triggered when an agent starts.

    Args:
        agent_name (str): Name of the agent that started.
        **kwargs: Additional event data.
    """
    print(f"Agent '{agent_name}' has started!")


def on_agent_ready(agent_name, **kwargs):
    """
    Callback function triggered when an agent is ready.

    Args:
        agent_name (str): Name of the agent that is ready.
        **kwargs: Additional event data.
    """
    print(f"Agent '{agent_name}' is ready!")


def on_agent_close(agent_name, **kwargs):
    """
    Callback function triggered when an agent terminates.

    Args:
        agent_name (str): Name of the agent that terminated.
        **kwargs: Additional event data.
    """
    print(f"Agent '{agent_name}' has terminated!")


if __name__ == "__main__":
    # Orchestrator initialization
    orchestrator = Orchestrator()

    # Register event callbacks directly on the orchestrator
    orchestrator.register_event(OrchestratorEvent.AGENT_STARTED, on_agent_start)
    orchestrator.register_event(OrchestratorEvent.AGENT_READY, on_agent_ready)
    orchestrator.register_event(OrchestratorEvent.AGENT_TERMINATED, on_agent_close)

    # Registering agents
    fetch_agent: AgentEntry = orchestrator.register_agent(
        APIFetchAgent, "APIFetchAgent"
    )

    # Starting agents
    orchestrator.start()

    # Waiting for agents to terminate
    orchestrator.join()
