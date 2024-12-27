from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.orchestrator.memory import AgentEntry
from PyOrchestrate.core.base.periodic_agent import PeriodicAgent
from PyOrchestrate.core.base.pool_agent import PoolAgent
from PyOrchestrate.core.base.base_agent import ProcessAgent, ThreadAgent
from PyOrchestrate.core.base.utilities import LoggerConfig


class MyThread(PeriodicAgent, ThreadAgent):
    class Config(PeriodicAgent.Config):
        limit: int = 3

    def runner(self):
        print(f"Thread {self.name} running")


class FileWriter(PoolAgent, ProcessAgent):
    class Config(PoolAgent.Config):
        agents_entry = [AgentEntry(MyThread, "Thread1"), AgentEntry(MyThread, "Thread2")]
        output_directory: str = "output"

    def setup(self):
        """
        Imposta il FileWriter, creando la directory di log se necessario.
        """
        super().setup()

        self.logger.info(f"FileWriter {self.name} inizializzato.")
        self.logger.info(f"Directory di output: {self.config.output_directory}")


if __name__ == "__main__":
    # orchestrator
    oConfig = Orchestrator.Config(logger_config=LoggerConfig("INFO", "Orchestrator"))
    orchestrator = Orchestrator(oConfig)

    # first agent with default configuration
    orchestrator.register_agent(FileWriter, "FileWriter1", )

    # start all agents
    orchestrator.start()

    # first report
    orchestrator.report()

    # wait for all agents to complete
    orchestrator.join()

    # second report
    orchestrator.report()
