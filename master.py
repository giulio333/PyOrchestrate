from multiprocessing import Process
from logging import Logger
from logger import setup_logger
from typing import Optional, List
from base import BaseConfig, BaseProcess, TConfig


class MasterProcess(BaseProcess[TConfig]):
    """Gestisce processi figli definiti dall'utente."""

    def __init__(
        self,
        name: str,
        config: TConfig,
    ) -> None:
        """
        Inizializza un'istanza di MasterProcess.

        Args:
        name (str): Nome del processo.
        config (TConfig): Configurazioni del processo.
        """
        super().__init__(name, config)

        self.children: List[BaseProcess] = []

        self.run()

    def add_child(self, child_instance: BaseProcess) -> None:
        """
        Aggiunge un'istanza di processo figlio.

        Args:
        child_instance (BaseProcess): Istanza del processo figlio da aggiungere.
        """
        self.children.append(child_instance)
        self.logger.info(f"Aggiunto figlio: {child_instance.name}")

    def start_all_children(self) -> None:
        """Avvia tutti i processi figli."""
        self.logger.info("Figli da avviare: %d", len(self.children))

        for child in self.children:
            child.start()
            self.logger.info(f"Avviato figlio: {child.name}")

    def wait_for_children(self) -> None:
        """Aspetta che tutti i processi figli terminino."""
        for child in self.children:
            child.join()
            self.logger.info(f"Figlio terminato: {child.name}")

    def stop_all_children(self) -> None:
        """Ferma tutti i processi figli."""
        for child in self.children:
            child.terminate()
            self.logger.warning(f"Figlio terminato forzatamente: {child.name}")
