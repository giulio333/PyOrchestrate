import time

from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.orchestrator.memory import AgentEntry
from PyOrchestrate.core.agent.periodic_agent import PeriodicThreadAgent
from PyOrchestrate.core.agent.pool_agent import PoolProcessAgent

# from multiprocessing import Queue
from queue import Queue


class MyThread(PeriodicThreadAgent):

    class Config(PeriodicThreadAgent.Config):
        """Thread agent configuration class."""

        execution_interval = 1
        limit = 5

    config: Config

    def setup(self):
        super().setup()

        self.media = 0
        self.counter = 0

    def runner(self) -> None:
        self.logger.info(f"Thread {self.name} writing to queue.")

        heavy_data = "a" * 1000000000

        _start = time.time()
        self.queue.put(heavy_data)
        self.media += time.time() - _start

        self.counter += 1

    def on_close(self):
        self.logger.info(f"Thread {self.name} media: {self.media/self.counter}")


class FileWriter(PoolProcessAgent):

    class Config(PoolProcessAgent.Config):
        """Process agent configuration class."""

        queue = Queue()
        execution_interval = 1
        agents_entry: list[AgentEntry] = [
            AgentEntry(MyThread, "MyThread", queue=queue),
        ]

    config: Config

    def setup(self) -> None:
        super().setup()
        self.logger.info(f"FileWriter {self.name} initialized.")

    def on_close(self):

        while not self.config.queue.empty():
            self.config.queue.get()
            self.logger.info("getting data from queue")


if __name__ == "__main__":
    orchestrator = Orchestrator()

    orchestrator.register_agent(FileWriter, f"FileWriter")

    orchestrator.start()
    orchestrator.join()
