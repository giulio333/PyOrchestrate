import time
from dataclasses import dataclass
from logging import DEBUG

from framework.slave import (
    ThreadPoolSlave,
    ThreadPoolSlaveConfig,
    LoggerConfig,
    CheckConfig,
)
from framework.worker import BaseConfig, BaseWorker
from framework.slave.threadpool_slave import w_config


class ww(BaseWorker):
    def work(self):
        self.logger.info(f"Hello, World!")

    def setup(self):
        self.logger.info(f"Configurazione: {self.config}")


c = w_config("worker", ww, BaseConfig())


@dataclass
class EngineConfig(ThreadPoolSlaveConfig):

    message: str = "Hello, World!"
    repeat: int = 50

    interval = 1
    compensate_delay = True

    logger = LoggerConfig(level="DEBUG")
    check_config = CheckConfig(to_monitor=True, autorestart=False)


class Engine(ThreadPoolSlave[EngineConfig]):

    def __init__(self, config: EngineConfig) -> None:
        super().__init__(config=config, workers=[c])

    def setup(self) -> None:
        super().setup()

        self.logger.info(f"Configurazione: {self.config}")

        self.frame_number = 0
