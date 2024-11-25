from logging import Logger
from multiprocessing import Process
from typing import TypeVar, Generic
from dataclasses import dataclass
import logging

from framework.logger import setup_logger


class BaseConfig:
    """
    Classe base per le configurazioni.
    """

    def validate(self) -> None:
        """Metodo per validare i parametri di configurazione."""
        pass


TConfig = TypeVar("TConfig", bound=BaseConfig)


class BaseProcess(Process, Generic[TConfig]):
    """Classe base per tutti i processi con un logger e configurazione opzionale."""

    def __init__(self, name: str, config: TConfig):
        super().__init__()
        self.name: str = name
        self.config: TConfig = config
        self.logger: Logger

    def run(self) -> None:

        if not hasattr(self, "logger"):
            self.logger = self.setup_logger(log_file=f"{self.name}.log")

        self.config.validate()

        self.work()

    def work(self) -> None:
        """
        Metodo principale da implementare nelle sottoclassi.
        """

        raise NotImplementedError(
            f"La classe '{self.__class__.__name__}' deve implementare il metodo `work`."
        )

    def setup_logger(self, log_file: str, level: int = logging.INFO) -> Logger:
        """
        Configura il logger del processo.

        E' possibile sovrascrivere questo metodo per personalizzare il logger.

        Args:
            log_file (str): Nome del file di log.
            level (int): Livello di log.

        Returns:
            Logger: Istanza del logger configurato.
        """

        return setup_logger(self.name, log_file, level)
