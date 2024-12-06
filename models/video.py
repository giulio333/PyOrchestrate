from framework.master import MasterProcess
from framework.child import ChildProcess
import time
from dataclasses import dataclass
from datetime import datetime
from logging import DEBUG

from framework.child import ChildConfig
from framework.utilities import LoggerConfig


@dataclass
class WorkerConfig1(ChildConfig):

    message: str = "Hello, World!"
    repeat: int = 5
    logger = LoggerConfig(level=DEBUG)
    to_monitor: bool = True
    autorestart: bool = True


@dataclass
class WorkerConfig2(ChildConfig):

    message: str = "Hello, World!"
    repeat: int = 5
    logger = LoggerConfig(level=DEBUG)
    to_monitor: bool = True
    autorestart: bool = True


class Worker(ChildProcess[WorkerConfig1]):

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


class Worker2(ChildProcess[WorkerConfig2]):

    def __init__(self, config: WorkerConfig2) -> None:
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
