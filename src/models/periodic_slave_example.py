import time
from dataclasses import dataclass
from logging import DEBUG

from framework.slave import PeriodicSlave, SlaveConfig, LoggerConfig, CheckConfig


@dataclass
class WorkerConfig1(SlaveConfig):

    message: str = "Hello, World!"
    repeat: int = 5

    logger = LoggerConfig(level=DEBUG)
    check_config = CheckConfig(to_monitor=True, autorestart=False)


@dataclass
class WorkerConfig2(SlaveConfig):

    message: str = "Hello, World!"
    repeat: int = 5

    logger = LoggerConfig(level=DEBUG)
    check_config = CheckConfig(to_monitor=False, autorestart=False)


class Worker(PeriodicSlave[WorkerConfig1]):

    def __init__(self, config: WorkerConfig1) -> None:
        super().__init__(config=config)

    def setup(self) -> None:
        self.logger.info(f"Configurazione: {self.config}")

    def runner(self) -> None:
        self.logger.info(
            f"Avvio elaborazione video: {self.config.message} repeat: {self.config.repeat}"
        )

        for i in range(self.config.repeat):
            self.logger.info(
                f"Elaborazione frame {i+1}/{self.config.repeat}: {self.config.message}"
            )
            # Simula l'elaborazione di un frame video
            time.sleep(0.5)

        self.stop_event.set()

        self.logger.info("Elaborazione video completata.")
