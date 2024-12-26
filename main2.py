import os
from dataclasses import dataclass
import time

from framework.core.orchestrator import Orchestrator
from framework.core.orchestrator.memory import AgentEntry
from framework.core.base.periodic_agent import PeriodicProcessAgent, PeriodicThreadAgent
from framework.core.base.utilities import LoggerConfig
from framework.core.base.pool_agent import PoolAgent


class MyThread(PeriodicThreadAgent):
    def runner(self):
        print(f"Thread {self.name} running")

        self.stop()


@dataclass
class FileWriterConfig(PeriodicProcessAgent.Config):
    agents_entry = [AgentEntry(MyThread, "Thread1")]
    output_directory = "log"
    num_iterations = 5


class FileWriter(PoolAgent):
    @dataclass
    class Config(FileWriterConfig):
        pass

    def setup(self):
        """
        Imposta il FileWriter, creando la directory di log se necessario.
        """
        super().setup()

        self.logger.info(f"FileWriter {self.name} inizializzato.")
        self.logger.info(f"Directory di output: {self.config.output_directory}")
        self.logger.info(f"Numero di iterazioni: {self.config.num_iterations}")


if __name__ == "__main__":
    # orchestrator
    oConfig = Orchestrator.Config(logger=LoggerConfig("INFO", "Orchestrator"))
    orchestrator = Orchestrator(oConfig)

    # first agent with default configuration
    orchestrator.register_agent(FileWriter, "FileWriter1")
    # FileWriter.Config(agents_entry=[AgentEntry(MyThread, "Thread1")]))

    # start all agents
    orchestrator.start()

    # first report
    orchestrator.report()

    # wait for all agents to complete
    orchestrator.join()

    # second report
    orchestrator.report()
