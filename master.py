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
            if child.is_alive():
                child.terminate()
                self.logger.warning(f"Figlio terminato forzatamente: {child.name}")
            else:
                self.logger.info(f"Figlio già terminato: {child.name}")

    def restart_all_children(self) -> None:
        """Riavvia tutti i processi figli."""
        for i, child in enumerate(self.children):
            if child.is_alive():
                child.terminate()
                self.logger.warning(f"Figlio terminato forzatamente: {child.name}")

            # Creare una nuova istanza del processo figlio
            new_child = type(child)(*child._args, **child._kwargs)
            self.children[i] = new_child
            new_child.start()
            self.logger.info(f"Riavviato figlio: {new_child.name}")

    def remove_child(self, child_name: str) -> None:
        """Rimuove un processo figlio specifico."""
        self.children = [child for child in self.children if child.name != child_name]
        self.logger.info(f"Rimosso figlio: {child_name}")

    def get_child_status(self, child_name: str) -> Optional[str]:
        """Ottiene lo stato di un processo figlio specifico."""
        for child in self.children:
            if child.name == child_name:
                return f"Processo {child_name} è {'attivo' if child.is_alive() else 'terminato'}"
        return None
