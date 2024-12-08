from logging import Logger
from multiprocessing import Process
from typing import TypeVar, Generic, Type
from dataclasses import dataclass
import logging
import time

from framework.utilities.logger import setup_logger
from framework.base_process.utilities import LoggerConfig
from framework.base_process.exceptions import TerminateProcess


class BaseConfig:
    """
    Classe base per le configurazioni.

    E' possibile estendere questa classe per aggiungere nuovi parametri di configurazione.

    Attributes:
        logger (LoggerConfig): Configurazioni del `logger`.

    Methods:
        validate: Metodo per validare i parametri di configurazione.
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
        super().__init__(name=name)

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
        super().run()

        self.start_time = time.time()

        self.setup_logger()

        self.check_process_config()

        try:
            self.work()
        except TerminateProcess as e:
            self.logger.warning("Processo terminato: %s", e)

        self.logger.debug("End - execution time[%.2f]", time.time() - self.start_time)

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

        # estrazione configurazioni da BaseConfig.LoggerConfig
        logger_config: LoggerConfig = self.config.logger
        level: int = logger_config.level
        name: str = logger_config.filename.capitalize() or self.name

        self.logger = setup_logger(name=name, log_file=f"{name}.log", level=level)

        self.logger.info(
            "Logger configurato: log_file=%s, level=%s",
            f"{self.name}.log",
            logging.getLevelName(level),
        )

    def check_process_config(self, config_class: Type[BaseConfig] = BaseConfig):
        """
        Metodo per controllare l'integrità delle configurazioni passate al processo.

        - Controlla che il processo abbia un attributo `config`.
        - Controlla che il tipo di configurazione sia coerente con il tipo di processo.
        - Esegue la validazione delle configurazioni.

        Args:
            config_class (Type[BaseConfig], optional): Tipo di configurazione assegnata.
        """

        if not hasattr(self, "config"):
            raise AttributeError("Il processo deve avere un attributo `config`.")

        if not isinstance(self.config, config_class):
            config_bases = ", ".join(
                base.__name__ for base in type(self.config).__bases__
            )
            process_bases = ", ".join(base.__name__ for base in type(self).__bases__)
            raise TypeError(
                f"Il tipo '{type(self.config).__name__}' (ereditato da {config_bases}) non è valido "
                f"per il processo di tipo '{type(self).__name__}' (ereditato da {process_bases}).\n"
                f"Il processo {process_bases} richiede un tipo di configurazione {process_bases+"Config"}."
            )

        self.config.validate()

        self.logger.debug("Configurazioni validate: %s", self.config)
