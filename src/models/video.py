from framework.slave.slave import SlaveProcess
import time
from dataclasses import dataclass
from logging import DEBUG

from framework.slave import SlaveProcess, SlaveConfig, LoggerConfig, CheckConfig


@dataclass
class WorkerConfig1(SlaveConfig):

    message: str = "Hello, World!"
    repeat: int = 5

    logger = LoggerConfig(level=DEBUG)
    check_config = CheckConfig(to_monitor=True, autorestart=True)


@dataclass
class WorkerConfig2(SlaveConfig):

    message: str = "Hello, World!"
    repeat: int = 5

    logger = LoggerConfig(level=DEBUG)
    check_config = CheckConfig(to_monitor=False, autorestart=False)


class Worker(SlaveProcess[WorkerConfig1]):

    def __init__(self, config: WorkerConfig1) -> None:
        super().__init__(config=config)

    def work(self) -> None:
        self.logger.info(
            f"Avvio elaborazione video: {self.config.message} repeat: {self.config.repeat}"
        )

        for i in range(self.config.repeat):
            self.logger.info(
                f"Elaborazione frame {i+1}/{self.config.repeat}: {self.config.message}"
            )
            # Simula l'elaborazione di un frame video
            time.sleep(0.5)

        self.logger.info("Elaborazione video completata.")
