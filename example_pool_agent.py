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

    def runner(self):
        self.logger.debug(f"Thread {self.name} running")


class FileWriter(PoolProcessAgent["FileWriter.Config"]):
    class Config(PoolProcessAgent.Config):
        agents_entry = [AgentEntry(MyThread, "DefaultThread", control_events=None, state_events=None)]
        auto_reboot = True

    def setup(self):
        """
        Imposta il FileWriter, creando la directory di log se necessario.
        """
        super().setup()
        self.logger.info(f"FileWriter {self.name} inizializzato.")


if __name__ == "__main__":
    # Configurazione dell'orchestratore
    oConfig = Orchestrator.Config(
        logger_config=LoggerConfig("INFO", "Orchestrator")
    )
    orchestrator = Orchestrator("Orchestrator")

    # Esempio 1: uso della config di default (senza passare agent_entry)
    a = orchestrator.register_agent(FileWriter, "FileWriter_Default")

    # Esempio 2: config custom con agent personalizzati
    fw2_config = FileWriter.Config(
        agents_entry=[
            AgentEntry(MyThread, "ThreadCustom1", control_events=None, state_events=None),
        ], auto_reboot=False
    )
    orchestrator.register_agent(FileWriter, "FileWriter_Custom", custom_config=fw2_config)

    # Avvio degli agent
    orchestrator.start()

    # Attendo la terminazione di tutti gli agent
    orchestrator.join()
