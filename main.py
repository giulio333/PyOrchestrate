from logging import INFO, Logger
from master import MasterProcess
from child import ChildProcess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
import logging

from base import BaseConfig


@dataclass
class WorkerConfig(BaseConfig):

    message: str = "Hello, World!"
    repeat: int = 10


class Worker(ChildProcess[WorkerConfig]):

    def __init__(self, config: WorkerConfig, name: str = "VideoWorker") -> None:
        """
        Inizializza un'istanza di Worker.

        Args:
        name (str): Nome del processo.
        config (MessagePrinterConfig): Configurazioni del processo.
        """
        super().__init__(name, config)

    def setup_logger(
        self, log_file: str = "Worker.log", level: int = logging.INFO
    ) -> Logger:
        return super().setup_logger(log_file, level)

    def work(self) -> None:
        """
        Metodo principale da implementare nelle sottoclassi.
        """
        self.logger.info(
            f"Avvio stampa messaggi: {self.config.message} repeat: {self.config.repeat}"
        )

        for _ in range(self.config.repeat):
            self.logger.info(self.config.message)

            time.sleep(0.5)

        self.logger.info("Stampa completata.")


@dataclass
class LauncherConfig(BaseConfig):
    version: str = "1.0"
    start_time: datetime = datetime.now()


class Launcher(MasterProcess[LauncherConfig]):
    def __init__(self, name: str, config: LauncherConfig) -> None:
        """
        Inizializza un'istanza di Launcher.

        Args:
        name (str): Nome del processo.
        config (LauncherConfig): Configurazioni del processo.
        """
        super().__init__(name, config)

    def setup_logger(
        self, log_file: str = "Launcher.log", level: int = logging.INFO
    ) -> Logger:
        return super().setup_logger(log_file, level)

    def work(self) -> None:
        """
        Metodo principale da implementare nelle sottoclassi.
        """

        self.logger.info("Master start.")
        self.logger.info(self.config)


if __name__ == "__main__":

    master = Launcher("Master", LauncherConfig())

    master.run()
    master.instantiate_children(Worker, WorkerConfig())
    master.start_children()

    time.sleep(2)

    master.restart_all_children()

    master.wait_for_children()

    print("Tutti i processi sono completati.")
