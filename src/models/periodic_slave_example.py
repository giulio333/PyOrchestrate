import time
from dataclasses import dataclass
from logging import DEBUG

from framework.core.slave import (
    PeriodicSlave,
    PeriodicSlaveConfig,
    LoggerConfig,
    CheckConfig,
)

from framework.core.base.exceptions import TerminateProcess


@dataclass
class WorkerConfig(PeriodicSlaveConfig):

    message: str = "Hello, World!"
    repeat: int = 50

    interval = 1
    compensate_delay = True

    logger = LoggerConfig(level="DEBUG")
    check_config = CheckConfig(to_monitor=True, autorestart=False)


class Worker(PeriodicSlave[WorkerConfig]):

    def __init__(self, config: WorkerConfig) -> None:
        super().__init__(config=config)

    def setup(self) -> None:
        super().setup()

        self.logger.info(f"Configurazione: {self.config}")

        self.frame_number = 0

    def runner(self) -> None:

        self.frame_number += 1

        self.logger.info(
            f"Elaborazione frame {self.frame_number}/{self.config.repeat}: {self.config.message}"
        )

        if self.frame_number > 9 and self.frame_number < 21:
            time.sleep(self.interval + 0.3)

        if self.frame_number >= self.config.repeat:
            self.logger.info("Elaborazione completata.")
            raise TerminateProcess()
