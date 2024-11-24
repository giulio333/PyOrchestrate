"""
Script di esempio utilizzo del framework.

L'utente crea un Master e un Child con le relative configurazioni.

Per creare una nuova configurazione, creare una nuova classe dataclass che erediti da BaseConfig.

Per creare un Master o un Child, creare una nuova classe che erediti da MasterProcess o ChildProcess
"""

from master import MasterProcess
from child import ChildProcess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from base import BaseConfig


@dataclass
class WorkerConfig(BaseConfig):

    message: str = "Hello, World!"
    repeat: int = 50


class Worker(ChildProcess[WorkerConfig]):

    def __init__(self, config: WorkerConfig, name: str = "VideoWorer") -> None:
        """
        Inizializza un'istanza di Worker.

        Args:
        name (str): Nome del processo.
        config (MessagePrinterConfig): Configurazioni del processo.
        """
        super().__init__(name, config)

    def work(self) -> None:
        """
        Metodo principale da implementare nelle sottoclassi.
        """
        self.logger.info(f"Avvio stampa messaggi: {self.config.message}")

        for _ in range(self.config.repeat):
            self.logger.info(self.config.message)

            time.sleep(0.5)

        self.logger.info("Stampa completata.")


@dataclass
class LauncherConfig(BaseConfig):
    version: str = "1.0"
    start_time: datetime = datetime.now()

    @property
    def elapsed_time(self) -> timedelta:
        """
        elapsed_time restituisce il tempo trascorso dall'avvio del processo.

        Returns:
            timedelta: Tempo trascorso dall'avvio del processo.
        """
        return datetime.now() - self.start_time


class Launcher(MasterProcess[LauncherConfig]):
    def __init__(self, name: str, config: LauncherConfig) -> None:
        """
        Inizializza un'istanza di Launcher.

        Args:
        name (str): Nome del processo.
        config (LauncherConfig): Configurazioni del processo.
        """
        super().__init__(name, config)

        self.instantiate_children(
            Worker, WorkerConfig(message="Hello, World!", repeat=5)
        )

    def work(self) -> None:
        """
        Metodo principale da implementare nelle sottoclassi.
        """
        self.logger.info("Master start.")
        self.logger.info(self.config)


if __name__ == "__main__":

    master = Launcher("Master", LauncherConfig())

    master.start_all_children()
    master.wait_for_children()

    # time.sleep(2)
    # master.restart_all_children()

    print("Tutti i processi sono completati.")
