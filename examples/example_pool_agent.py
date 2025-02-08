import time

from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.orchestrator.memory import AgentEntry
from PyOrchestrate.core.agent.periodic_agent import PeriodicThreadAgent
from PyOrchestrate.core.agent.pool_agent import PoolProcessAgent

# from multiprocessing import Queue
from queue import Queue


class ThreadConfig1(PeriodicThreadAgent.Config):
    """Thread agent configuration class."""

    execution_interval = 0.1
    limit = 5


class ThreadConfig2(PeriodicThreadAgent.Config):
    """Thread agent configuration class."""

    execution_interval = 1
    limit = 5


class MyThread(PeriodicThreadAgent[ThreadConfig1]):

    Config = ThreadConfig1

    def __init__(self, name: str, config: ThreadConfig1, queue, **kwargs):
        super().__init__(name, config, **kwargs)
        self.my_queue = queue

        self.media = 0
        self.counter = 0

    def runner(self) -> None:
        self.logger.debug(f"Thread {self.name} writing to queue.")

        heavy_data = "a" * 1000000000

        _start = time.time()
        self.my_queue.put(heavy_data)
        self.media += time.time() - _start

        self.counter += 1

    def on_close(self):
        self.logger.info(f"Thread {self.name} media: {self.media/self.counter}")


class FileWriterConfig(PoolProcessAgent.Config):
    """Process agent configuration class."""

    queue = Queue()
    execution_interval = 1
    agents_entry: list[AgentEntry] = [
        AgentEntry(MyThread, "MyThread1", queue=queue),
    ]


class FileWriter(PoolProcessAgent[FileWriterConfig]):

    Config = FileWriterConfig

    def __init__(self, name: str, config: FileWriterConfig, **kwargs):
        super().__init__(name, config, **kwargs)

    def setup(self) -> None:
        super().setup()
        self.logger.info(f"FileWriter {self.name} inizializzato.")

    def on_stop(self):
        while not self.config.queue.empty():
            try:
                self.config.queue.get_nowait()
            except:
                print("Queue is empty.")
                break


if __name__ == "__main__":
    orchestrator = Orchestrator()

    orchestrator.register_agent(FileWriter, f"FileWriter1")

    orchestrator.start()
    orchestrator.join()
