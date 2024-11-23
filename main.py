from master import MasterProcess
from child import ChildProcess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from base import BaseConfig


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

    def work(self) -> None:
        """
        Metodo principale da implementare nelle sottoclassi.
        """
        self.logger.info("Master start.")
        self.logger.info(self.config)


class MessagePrinterConfig(BaseConfig):

    def __init__(self, message: str, repeat: int) -> None:
        """
        Inizializza un'istanza di MessagePrinterConfig.

        Args:
        message (str): Messaggio da stampare.
        repeat (int): Numero di ripetizioni del messaggio.
        """
        super().__init__()

        self.message: str = message
        self.repeat: int = repeat

        self.count: int = 0


class MessagePrinter(ChildProcess[MessagePrinterConfig]):

    def __init__(self, name: str, config: MessagePrinterConfig) -> None:
        """
        Inizializza un'istanza di MessagePrinter.

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

            self.config.count += 1

            time.sleep(0.5)

        self.logger.info("Stampa completata. Totale messaggi: %d", self.config.count)


if __name__ == "__main__":

    master = Launcher("Master", LauncherConfig())

    # Configurazioni per i processi figli
    message_config = MessagePrinterConfig(message="Ciao Giulio!", repeat=5)

    # Creiamo i processi figli con le configurazioni
    child1 = MessagePrinter("MessagePrinter-1", config=message_config)

    # Aggiungiamo i processi figli al Master
    master.add_child(child1)

    # Avviamo i processi
    master.start_all_children()
    master.wait_for_children()

    print("Tutti i processi sono completati.")
