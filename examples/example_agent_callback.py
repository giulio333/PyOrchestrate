import time
import multiprocessing
import requests
import zmq

from PyOrchestrate.core.orchestrator import Orchestrator, AgentEntry
from PyOrchestrate.core.utilities.event_manager import EventManager
from PyOrchestrate.core.utilities.event import AgentEvent
from PyOrchestrate.core.agent import BaseProcessAgent
from PyOrchestrate.core.plugins.communication_plugins import ZeroMQPubSub


class MyConfig(BaseProcessAgent.Config):
    # URL of the example API (returns JSON data)
    api_url: str = "https://catfact.ninja/fact"
    # Keyword to search in the response
    keyword: str = "and"
    # Polling interval in seconds
    poll_interval: float = 1.0


class APIFetchAgent(BaseProcessAgent[MyConfig]):
    Config = MyConfig

    def setup(self) -> None:
        """
        Agent initialization: registers the communication plugin and logs the setup.
        """
        super().setup()
        zmq_plugin = ZeroMQPubSub("tcp://localhost:5555", zmq.PUB)
        self.plugin_manager.register(zmq_plugin)
        self.logger.info(f"Initializing APIFetchAgent with API: {self.config.api_url}")
        time.sleep(1)

    def execute(self) -> None:
        """
        Polls the external API and, if the keyword is found in the data,
        sends a message to the other agent.
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
                        self.com.ZeroMQPubSub.send(
                            f"Keyword '{self.config.keyword}' found: {message_str}"
                        )
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
            # At the end of the cycle, send a STOP signal to the other agent
            self.com.send_string("STOP")
            self.plugin_manager.unregister()

    def on_stop(self):
        """
        Logs the termination of the agent.
        """
        self.logger.info("APIFetchAgent terminated.")


class APIAlertAgent(BaseProcessAgent[MyConfig]):
    Config = MyConfig

    def setup(self) -> None:
        """
        Initializes the agent for receiving messages.
        """
        super().setup()
        zmq_plugin = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB)
        self.plugin_manager.register(zmq_plugin)
        # Set the log level to INFO
        self.config.logger_config.level = "INFO"
        self.logger.info(
            "Initializing APIAlertAgent for receiving alerts from the API."
        )

        time.sleep(3)

    def execute(self) -> None:
        """
        Listens for messages sent by APIFetchAgent.
        """
        super().execute()
        self.logger.info("Listening for messages from APIFetchAgent...")
        try:
            while True:
                message = self.com.recv_string()
                self.logger.success(f"Message received: {message}")
                if message == "STOP":
                    self.logger.info("Received STOP signal.")
                    break
        except Exception as e:
            self.logger.exception(f"Error receiving messages: {e}")
        finally:
            self.plugin_manager.unregister()

    def on_stop(self):
        """
        Logs the termination of the agent.
        """
        self.logger.info("APIAlertAgent terminated.")


def on_agent_started(event_date, event_time):
    message = f"Agent  started. Date: {event_date}, Time: {event_time}"
    print(message)


if __name__ == "__main__":
    # Required for multiprocessing support
    multiprocessing.set_start_method("spawn")

    # Orchestrator initialization
    orchestrator = Orchestrator()

    # Create an EventManager
    event_manager = EventManager()
    event_manager.connect(AgentEvent.AGENT_SETUP, on_agent_started)

    # Registering agents
    fetch_agent: AgentEntry = orchestrator.register_agent(
        APIFetchAgent, "APIFetchAgent", event_manager=event_manager
    )

    # Starting agents
    orchestrator.start()

    # Waiting for agents to terminate
    orchestrator.join()
