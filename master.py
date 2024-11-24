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
        self.children = {}
        self.original_configs = {}

        self.run()

    def instantiate_children(self, child_class: type, child_config: BaseConfig) -> None:
        """
        Args:
            child_class (type): Classe del processo figlio.
            child_config (BaseConfig): Configurazioni del processo figlio.
        """
        child_instance = child_class(config=child_config)
        self.children[child_instance.name] = child_instance
        self.original_configs[child_instance.name] = child_config
        self.logger.info(f"Aggiunto figlio: {child_instance.name}")

    def start_all_children(self) -> None:
        """Avvia tutti i processi figli."""
        self.logger.info("Figli da avviare: %d", len(self.children))

        for child_name, child_instance in self.children.items():
            child_instance.start()
            self.logger.info(f"Avviato figlio: {child_name}")

    def wait_for_children(self) -> None:
        """Aspetta che tutti i processi figli terminino."""
        for child in self.children:
            child.join()
            self.logger.info(f"Figlio terminato: {child.name}")

    def stop_all_children(self) -> None:
        """Ferma tutti i processi figli."""
        for child in self.children.values():
            if child.is_alive():
                child.terminate()
                self.logger.warning(f"Figlio terminato forzatamente: {child.name}")
            else:
                self.logger.info(f"Figlio già terminato: {child.name}")

    def restart_all_children(self) -> None:
        """Riavvia tutti i processi figli."""

        self.stop_all_children()

        for child_name, child_instance in self.children.items():
            self.instantiate_children(
                child_class=child_instance.__class__,
                child_config=self.original_configs[child_name],
            )

        self.start_all_children()

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

    def save_child_config(self, child_name: str, child_config: BaseConfig) -> None:
        """
        Salva la configurazione originale di un processo figlio.

        Args:
            child_name (str): Nome del processo figlio.
            child_config (BaseConfig): Configurazioni del processo figlio.
        """
        self.original_configs[child_name] = child_config
        self.logger.info(f"Configurazione salvata per il figlio: {child_name}")
