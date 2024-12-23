import os, sys
from dataclasses import dataclass

from src.framework.core.base.periodic_agent import PeriodicProcessAgent
from src.framework.core.orchestrator import Orchestrator


class FileWriter(PeriodicProcessAgent):
    @dataclass
    class Config(PeriodicProcessAgent.Config):
        num_iterations: int = 5
        execution_interval: float = 0.05
        delay_compensation: bool = True

    def runner(self):
        self.Config.num_iterations -= 1

        if self.Config.num_iterations == 0:
            self.stop()

        with open(f"{self.name}_log.txt", "a") as log_file:
            log_message = "ciao\n"
            log_file.write(log_message)

        self.logger.debug(log_message.strip())


if __name__ == "__main__":
    o = Orchestrator()

    o.add_agent(
        FileWriter,
        "AgentThread",
    )

    o.add_agent(
        FileWriter,
        name="AgentThread_veloce",
    )

    o.start()
    o.join()
