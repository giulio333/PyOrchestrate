import requests
import json
import os

from PyOrchestrate.core.base.base_agent import ProcessAgent
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.base.periodic_agent import PeriodicAgent
from PyOrchestrate.core.base.exceptions import RecoverableException

from PyOrchestrate.core.utilities.event import OrchestratorEvent


def on_agent_started(agent_name: str):
    print(f"Agent {agent_name} started.")


class WeatherCollector(PeriodicAgent["WeatherCollector.Config"], ProcessAgent["WeatherCollector.Config"]):
    """
    Example of a WeatherCollector agent that makes a request to an API and saves the data in a file.

    This is a Periodic and Process agent that makes a request to an API and saves the data in a file.
    """

    class Config(PeriodicAgent.Config):

        limit: int = 2
        execution_interval: float = 2
        url: str = "https://catfact.ninja/fact"
        output_file: str = "weather_data.json"
        print_result: bool = False

    def setup(self):
        """
        Initial setup of the WeatherCollector.
        """
        super().setup()
        self.logger.info("Configurazione iniziale del WeatherCollector...")
        if not os.path.exists(self.config.output_file):
            with open(self.config.output_file, "w") as file:
                json.dump([], file)  # type: ignore
            self.logger.info(f"Creato file di output: {self.config.output_file}")

    def runner(self):
        """
        Periodic logic (makes a request to the API and saves the data in a file).
        """
        self.logger.info(f"Making request to {self.config.url}...")

        try:
            response = requests.get(self.config.url)
            response.raise_for_status()
            data = response.json()

            with open(self.config.output_file, "r+") as file:
                records = json.load(file)
                records.append(data)
                file.seek(0)
                json.dump(records, file, indent=4)  # type: ignore

            self.logger.info(f"Dati salvati correttamente in {self.config.output_file}.")

            if self.config.print_result:
                self.logger.info(f"Risultato: {data}")

        except requests.RequestException as e:
            raise RecoverableException(f"Errore nella richiesta: {e}")


if __name__ == "__main__":
    orchestrator = Orchestrator("Orchestrator")

    orchestrator.register_agent(WeatherCollector, "WeatherCollector1")
    orchestrator.event_manager.connect(OrchestratorEvent.AGENT_STARTED.value, on_agent_started)

    orchestrator.start()
    orchestrator.join()
