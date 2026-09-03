from PyOrchestrate.core.orchestrator import Orchestrator, RunMode
from PyOrchestrate.core.agent.periodic_agent import PeriodicProcessAgent


class FileWriter(PeriodicProcessAgent):
    """Agent Class that logs a message periodically."""

    class Config(PeriodicProcessAgent.Config):
        """Process agent configuration class."""

        limit = 10
        execution_interval = 1
        directory = "/tmp"

    config: Config

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
    # Configure orchestrator
    config = Orchestrator.Config(
        enable_command_interface=True,
        command_zmq_address="tcp://127.0.0.1:5555",
        run_mode=RunMode.DAEMON,
        allowed_commands={"ps", "shutdown"},
    )
    orchestrator = Orchestrator(config=config)

    # register agents
    orchestrator.register_agent(FileWriter, "FileWriter1")

    custom_config = FileWriter.Config(execution_interval=2)
    orchestrator.register_agent(
        FileWriter,
        "FileWriter2",
        custom_config=custom_config,
    )

    # start agent
    orchestrator.start()

    # wait for agent to complete
    orchestrator.join()
