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


class ThreadConfig(PeriodicWorkerConfig):

    interval = 1
    cicli = 0


class PrinterThread(PeriodicWorker[ThreadConfig]):
    def runner(self):
        self.logger.info(f"Hello, World!")

        self.config.cicli += 1

        if self.config.cicli == 10:
            self.stop()


printer = w_config(PrinterThread, ThreadConfig())


class ReaderThread(PeriodicWorker[ThreadConfig]):

    def runner(self):
        self.logger.info(f"Lettura di un file")

        self.config.cicli += 1

        if self.config.cicli == 10:
            self.stop()


reader = w_config(ReaderThread, ThreadConfig())


@dataclass
class PrinterConfig(ThreadPoolSlaveConfig):

    message: str = "Hello, World!"
    repeat: int = 50

    interval = 1
    compensate_delay = True

    logger = LoggerConfig(level="DEBUG")
    check_config = CheckConfig(to_monitor=True, autorestart=False)


class Engine(ThreadPoolSlave[PrinterConfig]):

    def __init__(self, config: PrinterConfig) -> None:
        super().__init__(config=config, workers=[reader])

    def setup(self) -> None:
        super().setup()

        self.logger.info(f"Configurazione: {self.config}")

        self.frame_number = 0
