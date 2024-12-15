import time
from dataclasses import dataclass
from logging import DEBUG

from framework.slave import (
    ThreadPoolSlave,
    ThreadPoolSlaveConfig,
    LoggerConfig,
    CheckConfig,
)
from framework.worker import PeriodicWorker, PeriodicWorkerConfig
from framework.slave.threadpool_slave import w_config


class PrinterThread(PeriodicWorker):
    def runner(self):
        self.logger.info(f"Hello, World!")


printer = w_config("printer", PrinterThread, PeriodicWorkerConfig())


class ReaderThread(PeriodicWorker):
    def runner(self):
        self.logger.info(f"Lettura di un file")


reader = w_config("reader", ReaderThread, PeriodicWorkerConfig())


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
        super().__init__(config=config, workers=[reader, printer])

    def setup(self) -> None:
        super().setup()

        self.logger.info(f"Configurazione: {self.config}")

        self.frame_number = 0
