import os
from dataclasses import dataclass
import time

from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.base.periodic_agent import PeriodicAgent
from PyOrchestrate.core.base.base_agent import BaseProcessAgent
from PyOrchestrate.core.base.utilities import LoggerConfig





class FileWriter(PeriodicAgent, BaseProcessAgent):
    """
    FileWriter, un agente periodico che esegue un ciclo per scrivere log.
    """

    class Config(PeriodicAgent.Config):
        def __init__(self, output_directory: str="co", logger: LoggerConfig = LoggerConfig("INFO")):
            super().__init__()
            self.output_directory: str = output_directory
            self.logger = logger
            self.limit: int = 3

        def validate(self):
            pass

    def setup(self):
        """
        Imposta il FileWriter, creando la directory di log se necessario.
        """
        super().setup()

        self.logger.info(f"FileWriter {self.name} inizializzato.")
        self.logger.info(f"Directory di output: {self.config.output_directory}")

    def runner(self):
        log_message = f"Iterazione completata per {self.name}\n"
        self.logger.debug(log_message.strip())


if __name__ == "__main__":
    # orchestrator
    oConfig = Orchestrator.Config(logger_config=LoggerConfig("INFO", "Orchestrator"))
    orchestrator = Orchestrator(oConfig)

    # first agent with default configuration
    orchestrator.register_agent(FileWriter, "FileWriter1")

    # second agent with custom configuration
    custom_config = FileWriter.Config(output_directory="output", logger=LoggerConfig("DEBUG"))
    orchestrator.register_agent(FileWriter, "FileWriter2", custom_config)

    # start all agents
    orchestrator.start()

    # first report
    orchestrator.report()

    # wait for all agents to complete
    orchestrator.join()

    # second report
    orchestrator.report()
