from logging import Logger
from multiprocessing import Process
from typing import TypeVar, Generic
from dataclasses import dataclass
import logging
import time

from framework.logger import setup_logger
from framework.utilities import LoggerConfig


class BaseConfig:
    """
    Classe base per le configurazioni.
    """

    logger: LoggerConfig = LoggerConfig()

    def validate(self) -> None:
        """Metodo per validare i parametri di configurazione."""
        pass


Config = TypeVar("Config", bound=BaseConfig)


class BaseProcess(Process, Generic[Config]):
    """
    Classe base per tutti i processi.
    """

    def __init__(self, name: str, config: Config, *args, **kwargs):
        """
        Inizializza un'istanza di BaseProcess.

        Args:
            name (str): Nome del processo.
            config (Config): Configurazioni del processo.
        """
        super().__init__()

        self.name: str = name
        self.config: Config = config
        self.logger: Logger

    def run(self) -> None:
        """
        Metodo principale del processo.

        - Configura il logger con il nome del processo.
        - Esegue la validazione delle configurazioni.
        - Chiama il metodo `work`.
        """

        self.start_time = time.time()

        self.setup_logger()

        self.setup()

        self.config.validate()

        self.work()

        self.logger.debug("Tempo di esecuzione: %.2f", time.time() - self.start_time)

    def setup(self):
        """
        Metodo per l'inizializzazione delle risorse del processo.

        E' possibile sovrascrivere questo metodo per personalizzarne il comportamento.
        """

    def work(self) -> None:
        """
        Metodo principale da implementare nelle sottoclassi.
        """

        raise NotImplementedError(
            f"La classe '{self.__class__.__name__}' deve implementare il metodo `work`."
        )

    def setup_logger(self):
        """
        Configura il logger del processo.

        E' possibile sovrascrivere questo metodo per personalizzare il logger.

        Returns:
            Logger: Istanza del logger configurato.
        """

        if hasattr(self, "logger"):
            return

        level = self.config.logger.level or logging.INFO
        name = self.config.logger.filename or self.name

        self.logger = setup_logger(name=name, log_file=f"{name}.log", level=level)

        self.logger.info(
            "Logger configurato: log_file=%s, level=%s", f"{self.name}.log", level
        )
