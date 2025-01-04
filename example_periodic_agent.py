from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.base.periodic_agent import PeriodicAgent
from PyOrchestrate.core.base.base_agent import ProcessAgent
from PyOrchestrate.core.orchestrator.memory import AgentEntry


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
        self.logger.info(f"FileWriter {self.name} initialized. pid={self.pid}")

    def runner(self):
        """
        Runner method for the agent.
        """
        self.logger.info("Doing some work")


class FileReader(PeriodicAgent["FileReader.Config"], ProcessAgent["FileReader.Config"]):
    """Agent Class that reads from a file periodically."""

    class Config(PeriodicAgent.Config):
        """Agent Configuration class."""

        limit = 5
        execution_interval = 1
        input_directory = "input"
        file_writer_ready_event = None

    def setup(self):
        """
        Setup method for the agent.
        """
        super().setup()
        self.logger.info(f"FileReader {self.name} inizializzato. pid={self.pid}")

    def runner(self):
        """
        Runner method for the agent.
        """

        # check if FileWriter is running
        if self.config.file_writer_ready_event is not None and self.config.file_writer_ready_event.is_set():
            self.logger.info("FileWriter is ready.")

        else:
            self.logger.info("FileWriter is not ready yet.")
            return

        self.logger.info("Doing some work")


if __name__ == "__main__":
    orchestrator = Orchestrator("CoolOrchestrator")

    # register agents
    fw_agent: AgentEntry = orchestrator.register_agent(FileWriter, "FileWriter")

    # second agent with custom configuration
    custom_config = FileReader.Config(execution_interval=2, file_writer_ready_event=fw_agent.state_events.ready_event)
    orchestrator.register_agent(FileReader, "FileReader", custom_config)

    # start all agents
    orchestrator.start()

    # wait for all agents to complete
    orchestrator.join()
