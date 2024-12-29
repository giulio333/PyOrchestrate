from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.base.periodic_agent import PeriodicAgent
from PyOrchestrate.core.base.base_agent import ProcessAgent
from PyOrchestrate.core.base.utilities import LoggerConfig


class FileWriter(PeriodicAgent["FileWriter.Config"], ProcessAgent["FileWriter.Config"]):
    """Agent Class of type PeriodicAgent and ProcessAgent."""

    class Config(PeriodicAgent.Config):
        """Agent Configuration class."""

        limit = 5
        execution_interval = 1
        output_directory = "output"

    def setup(self):
        """
        Imposta il FileWriter, creando la directory di log se necessario.
        """
        super().setup()

        self.logger.info(f"FileWriter {self.name} inizializzato.")
        self.logger.info(f"Directory di output: {self.config.output_directory}")

    def runner(self):
        self.logger.debug("Doing some work")


if __name__ == "__main__":
    # orchestrator
    OConfig = Orchestrator.Config(check=True)
    orchestrator = Orchestrator("Orchestrator", OConfig)

    # first agent with default configuration
    orchestrator.register_agent(FileWriter, "FileWriter1")

    # second agent with custom configuration
    custom_config = FileWriter.Config(execution_interval=.1, limit=40)
    orchestrator.register_agent(FileWriter, "FileWriter2", custom_config)

    # start all agents
    orchestrator.start()

    # first report
    orchestrator.report()

    # wait for all agents to complete
    orchestrator.join()

    # second report
    orchestrator.report()
