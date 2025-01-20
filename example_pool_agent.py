import time

from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.orchestrator.memory import AgentEntry
from PyOrchestrate.core.base.periodic_agent import PeriodicThreadAgent
from PyOrchestrate.core.base.pool_agent import PoolProcessAgent
from PyOrchestrate.core.base.utilities import LoggerConfig
from multiprocessing import Queue


class ThreadConfig(PeriodicThreadAgent.Config):
    """Thread agent configuration class."""

    execution_interval = 0.1
    limit = 5


class MyThread(PeriodicThreadAgent[ThreadConfig]):

    Config = ThreadConfig

    def runner(self) -> None:
        self.logger.debug(f"Thread {self.name} writing to queue.")
        self.queue.put("Hello")


class OtherThread(PeriodicThreadAgent[ThreadConfig]):
    Config = ThreadConfig

    def runner(self) -> None:
        _ = self.queue.get()
        self.logger.debug(f"Thread {self.name} received {_}")


class FileWriterConfig(PoolProcessAgent.Config):
    """Process agent configuration class."""

    queue = Queue()
    execution_interval = 0.1
    agents_entry: list[AgentEntry] = [
        AgentEntry(MyThread, "MyThread1", queue=queue),
        AgentEntry(OtherThread, "OtherThread1", queue=queue),
    ]


class FileWriter(PoolProcessAgent[FileWriterConfig]):

    Config = FileWriterConfig

    def setup(self) -> None:
        super().setup()
        self.logger.info(f"FileWriter {self.name} inizializzato.")


if __name__ == "__main__":
    orchestrator = Orchestrator()

    orchestrator.register_agent(FileWriter, f"FileWriter1")

    orchestrator.start()
    orchestrator.join()
