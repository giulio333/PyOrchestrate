from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.orchestrator.memory import AgentEntry
from PyOrchestrate.core.base.periodic_agent import PeriodicAgent
from PyOrchestrate.core.base.pool_agent import PoolAgent
from PyOrchestrate.core.base.base_agent import ProcessAgent, ThreadAgent
from PyOrchestrate.core.base.utilities import LoggerConfig


class MyThread(PeriodicAgent, ThreadAgent):
    class Config(PeriodicAgent.Config):
        def __init__(self, limit: int = 5, **kwargs):
            super().__init__(limit=limit, execution_interval=.2, **kwargs)

    def runner(self):
        self.logger.debug(f"Thread {self.name} running")


class FileWriter(PoolAgent["FileWriter.Config"], ProcessAgent["FileWriter.Config"]):
    class Config(PoolAgent.Config):
        def __init__(self,
                     agents_entry=None,
                     default_agents=None,
                     **kwargs):
            if default_agents is None:
                # Esempio di set di agent di default
                default_agents = [
                    AgentEntry(MyThread, "DefaultThread1"),
                    AgentEntry(MyThread, "DefaultThread2")
                ]
            if agents_entry is None:
                agents_entry = default_agents

            super().__init__(agents_entry=agents_entry, **kwargs)

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
    orchestrator = Orchestrator("Orchestrator", oConfig)

    # Esempio 1: uso della config di default (senza passare agent_entry)
    orchestrator.register_agent(FileWriter, "FileWriter_Default")

    # Esempio 2: config custom con agent personalizzati
    fw2_config = FileWriter.Config(
        agents_entry=[
            AgentEntry(MyThread, "ThreadCustom1"),
            AgentEntry(MyThread, "ThreadCustom2")
        ]
    )
    orchestrator.register_agent(FileWriter, "FileWriter_Custom", custom_config=fw2_config)

    # Avvio degli agent
    orchestrator.start()
    orchestrator.report()

    # Attendo la terminazione di tutti gli agent
    orchestrator.join()
    orchestrator.report()
