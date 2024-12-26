from dataclasses import dataclass, field

from framework.core.orchestrator import Orchestrator
from framework.core.orchestrator.memory import AgentEntry
from framework.core.base.periodic_agent import PeriodicAgent
from framework.core.base.pool_agent import PoolAgent
from framework.core.base.baseagent import BaseProcessAgent, BaseThreadAgent
from framework.core.base.utilities import LoggerConfig


class MyThread(PeriodicAgent, BaseThreadAgent):
    class Config(PeriodicAgent.Config):
        limit: int = 3

    def runner(self):
        print(f"Thread {self.name} running")


class FileWriter(PoolAgent, BaseProcessAgent):
    class Config(PoolAgent.Config):
        agents_entry = [AgentEntry(MyThread, "Thread1"), AgentEntry(MyThread, "Thread2")]
        output_directory: str = field(default="output")

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
    orchestrator.register_agent(FileWriter, "FileWriter1")

    # start all agents
    orchestrator.start()

    # first report
    orchestrator.report()

    # wait for all agents to complete
    orchestrator.join()

    # second report
    orchestrator.report()
