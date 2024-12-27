import requests
import json
import os

from PyOrchestrate.core.base import BaseProcessAgent
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.base.periodic_agent import PeriodicAgent
from PyOrchestrate.core.base.utilities import LoggerConfig


class WeatherCollector(PeriodicAgent, BaseProcessAgent):
    """
    Makes a request to an API and saves the data in a file.
    """

    class Config(PeriodicAgent.Config):
        def __init__(self, output_file: str = "weather_data.json", url:str="https://catfact.ninja/fact"):
            super().__init__()
            self.output_file = output_file
            self.url = url

            # PeriodicAgent data
            self.limit = 5
            self.execution_interval = 5
            self.logger = LoggerConfig(level="INFO")

        def validate(self):
            pass

    def setup(self):
        """
        Initial setup of the WeatherCollector.
        """
        super().setup()
        self.logger.info("Configurazione iniziale del WeatherCollector...")
        if not os.path.exists(self.config.output_file):
            with open(self.config.output_file, "w") as file:
                json.dump([], file)  # Inizializza il file come lista vuota
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
                json.dump(records, file, indent=4)

            self.logger.info(f"Dati salvati correttamente in {self.config.output_file}.")

        except requests.RequestException as e:
            self.logger.error(f"Errore nella richiesta API: {e}")


if __name__ == "__main__":
    orchestrator = Orchestrator()

    orchestrator.register_agent(WeatherCollector, "WeatherCollector1")

    orchestrator.start()
    orchestrator.join()
