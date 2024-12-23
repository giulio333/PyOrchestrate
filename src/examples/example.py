import time
import os, sys
from time import sleep
from dataclasses import dataclass

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from framework.core.base.periodic_agent import PeriodicProcessAgent # type: ignore
from framework.core.orchestrator import Orchestrator # type: ignore


class FileWriter(PeriodicProcessAgent):

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    @dataclass
    class Config(PeriodicProcessAgent.Config):
        num_iterations: int = 5
        interval: float = 0.05
        compensate_delay: bool = True



    def runner(self):

        self.Config.num_iterations -= 1

        if self.Config.num_iterations == 0:
            self.stop()

        with open(f"{self.name}_log.txt", "a") as log_file:
            log_message = f"[{self.name}] ciao\n"
            log_file.write(log_message)

        self.logger.debug(log_message.strip())


if __name__ == "__main__":

    o = Orchestrator()

    o.add_agent(
        FileWriter,
        name="AgentThread1",
        custom_config={"interval": 1},
    )

    o.add_agent(
        FileWriter,
        name="AgentThread2",
    )

    o.start()
    o.join()
