import time
from dataclasses import dataclass
from logging import DEBUG

from framework.core.slave import (
    ThreadPoolSlave,
    ThreadPoolSlaveConfig,
    LoggerConfig,
    CheckConfig,
)
from framework.core.worker import PeriodicWorker, PeriodicWorkerConfig
from framework.core.slave.threadpool_slave import w_config


@dataclass
class PrinterThreadConfig(PeriodicWorkerConfig):

    interval: int = 1
    cicli: int = 0


class PrinterThread(PeriodicWorker[PrinterThreadConfig]):
    def runner(self):
        self.logger.info(f"Hello, World!")

        self.config.cicli += 1

        if self.config.cicli == 10:
            self.stop()


printer = w_config(PrinterThread, PrinterThreadConfig())


@dataclass
class PrinterConfig(ThreadPoolSlaveConfig):

    message: str = "Hello, World!"
    repeat: int = 50

    interval = 1
    compensate_delay = True

    logger = LoggerConfig(level="TRACE")
    check_config = CheckConfig(to_monitor=False, autorestart=False)


class PrinterPool(ThreadPoolSlave[PrinterConfig]):

    def __init__(self, config: PrinterConfig) -> None:
        super().__init__(config=config, workers=[printer])

    def setup(self) -> None:
        super().setup()

        self.logger.info(f"Configurazione: {self.config}")

        self.frame_number = 0
