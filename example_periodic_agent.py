from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.base.periodic_agent import PeriodicAgent
from PyOrchestrate.core.base.base_agent import ProcessAgent


class FileWriter(PeriodicAgent["FileWriter.Config"], ProcessAgent["FileWriter.Config"]):
    """Agent Class that writes to a file periodically."""

    class Config(PeriodicAgent.Config):
        """Agent Configuration class."""

        limit = 5
        execution_interval = 1
        output_directory = "output"

    def setup(self):
        """
        Setup method for the agent.
        """
        super().setup()
        self.logger.info(f"FileWriter {self.name} inizializzato. pid={self.pid}")

    def runner(self):
        """
        Runner method for the agent.
        """
        self.logger.debug("Doing some work")


if __name__ == "__main__":
    orchestrator = Orchestrator("CoolOrchestrator")

    # register agents
    orchestrator.register_agent(FileWriter, "FileWriter1")

    # second agent with custom configuration
    custom_config = FileWriter.Config(execution_interval=.1, limit=5)
    orchestrator.register_agent(FileWriter, "FileWriter2", custom_config, start_delay=20)

    # start all agents
    orchestrator.start()

    # wait for all agents to complete
    orchestrator.join()
