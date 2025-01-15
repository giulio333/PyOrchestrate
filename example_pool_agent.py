import time

from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.orchestrator.memory import AgentEntry
from PyOrchestrate.core.base.periodic_agent import PeriodicThreadAgent
from PyOrchestrate.core.base.pool_agent import PoolProcessAgent
from PyOrchestrate.core.base.utilities import LoggerConfig


class MyThread(PeriodicThreadAgent):
    class Config(PeriodicThreadAgent.Config):
        limit = 5
        execution_interval = .2
        logger_config = LoggerConfig(level="INFO")

    def runner(self):
        self.logger.debug(f"Thread {self.name} running")


class FileWriter(PoolProcessAgent["FileWriter.Config"]):
    class Config(PoolProcessAgent.Config):
        agents_entry = [
            AgentEntry(MyThread, "DefaultThread")]
        auto_reboot = True

    def setup(self):
        """
        Imposta il FileWriter, creando la directory di log se necessario.
        """
        super().setup()
        self.logger.info(f"FileWriter {self.name} inizializzato.")


if __name__ == "__main__":
    orchestrator = Orchestrator()

    a = orchestrator.register_agent(FileWriter, "FileWriter_Default")

    orchestrator.start()
    orchestrator.join()
