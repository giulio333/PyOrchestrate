from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.base.periodic_agent import PeriodicProcessAgent


class FileWriterConfig(PeriodicProcessAgent.Config):
    """Process agent configuration class."""

    limit = 5
    execution_interval = 1
    directory = "/tmp"


class FileWriter(PeriodicProcessAgent[FileWriterConfig]):
    """Agent Class that logs a message periodically."""

    Config = FileWriterConfig

    def setup(self):
        """
        Setup method for the agent.
        """
        super().setup()
        self.logger.info(f"FileWriter {self.name} initialized. pid={self.pid}")
        self.logger.info(f"Working with directory: {self.config.directory}")

    def runner(self):
        """
        Runner method for the agent.
        """
        self.logger.info("Doing some work")


if __name__ == "__main__":
    orchestrator = Orchestrator("CoolOrchestrator")

    # register agents
    orchestrator.register_agent(FileWriter, "FileWriter")

    # start agent
    orchestrator.start()

    # wait for agent to complete
    orchestrator.join()
