from framework.master import MasterProcess
from framework.child import ChildProcess
import time
from dataclasses import dataclass
from datetime import datetime
from logging import DEBUG

from framework.base import BaseConfig
from framework.utilities import LoggerConfig


@dataclass
class WorkerConfig(BaseConfig):

    message: str = "Hello, World!"
    repeat: int = 10
    logger = LoggerConfig(level=DEBUG)


class Worker2(ChildProcess[WorkerConfig]):

    def __init__(self, config: WorkerConfig, name: str = "VideoWorker2") -> None:
        super().__init__(name, config)

    def work(self) -> None:

        self.logger.info(
            f"Avvio stampa messaggi: {self.config.message} repeat: {self.config.repeat}"
        )

        for _ in range(self.config.repeat):
            self.logger.info(self.config.message)

            time.sleep(0.5)

        self.logger.info("Stampa completata.")


class Worker1(ChildProcess[WorkerConfig]):

    def __init__(self, config: WorkerConfig, name: str = "VideoWorker1") -> None:
        super().__init__(name, config)

    def work(self) -> None:
        self.logger.info(
            f"Avvio stampa messaggi: {self.config.message} repeat: {self.config.repeat}"
        )

        for _ in range(self.config.repeat):
            self.logger.info(self.config.message)

            time.sleep(0.5)

        self.logger.info("Stampa completata.")
