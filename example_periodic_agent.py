import os
from dataclasses import dataclass
import time

from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.base.periodic_agent import PeriodicAgent
from PyOrchestrate.core.base.base import BaseProcessAgent
from PyOrchestrate.core.base.utilities import LoggerConfig


@dataclass
class FileWriterConfig(PeriodicAgent.Config):
    num_iterations: int = 5
    output_directory: str = "./logs"
    logger = LoggerConfig(level="DEBUG")

    def validate(self):
        if self.num_iterations <= 0:
            raise ValueError("Il numero di iterazioni deve essere maggiore di 0.")


class FileWriter(PeriodicAgent, BaseProcessAgent):
    """
    FileWriter, un agente periodico che esegue un ciclo per scrivere log.
    """

    @dataclass
    class Config(FileWriterConfig):
        pass

    def setup(self):
        """
        Imposta il FileWriter, creando la directory di log se necessario.
        """
        super().setup()
        os.makedirs(self.config.output_directory, exist_ok=True)

        self.logger.info(f"FileWriter {self.name} inizializzato.")
        self.logger.info(f"Directory di output: {self.config.output_directory}")
        self.logger.info(f"Numero di iterazioni: {self.config.num_iterations}")

    def runner(self):
        if self.config.num_iterations <= 0:
            self.stop()
            return

        self.config.num_iterations -= 1
        log_message = f"Iterazione completata per {self.name}\n"
        file_path = os.path.join(self.config.output_directory, f"{self.name}_log.txt")

        with open(file_path, "a") as log_file:
            log_file.write(log_message)

        self.logger.debug(log_message.strip())


if __name__ == "__main__":
    # orchestrator
    oConfig = Orchestrator.Config(logger_config=LoggerConfig("INFO", "Orchestrator"))
    orchestrator = Orchestrator(oConfig)

    # first agent with default configuration
    orchestrator.register_agent(FileWriter, "FileWriter1")

    # second agent with custom configuration
    custom_config = FileWriter.Config(num_iterations=2, execution_interval=.5, output_directory="logs")
    orchestrator.register_agent(FileWriter, "FileWriter2", custom_config)

    # start all agents
    orchestrator.start()

    # first report
    orchestrator.report()

    # wait for all agents to complete
    orchestrator.join()

    # second report
    orchestrator.report()
