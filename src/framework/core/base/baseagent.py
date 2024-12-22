import multiprocessing
import threading
from abc import ABC, abstractmethod
import logging
import time
import os, sys
from dataclasses import dataclass
from loguru import logger
from dataclasses import dataclass

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from framework.utilities.logguru import LoggerFactory
from framework.core.base.utilities import LoggerConfig

import threading
import multiprocessing
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass


class BaseConfig(ABC):
    """
    Classe base per la configurazione.
    """

    logger: LoggerConfig = LoggerConfig()

    @classmethod
    def validate(cls):
        """Valida la configurazione."""
        pass


class AbstractBaseAgent(ABC):
    """
    Classe astratta che racchiude la logica comune a tutti gli agenti:
    - setup del logger
    - validazione della configurazione
    - metodo astratto execute
    """

    @dataclass
    class Config(BaseConfig):
        """
        Configurazione dell'agente.

        Attributes:
            logger (LoggerConfig): Configurazione del logger.
        """

    def __init__(self, name: str | None = None, *args, **kwargs):

        self.config = self.Config()
        self.name: str = name or self.__class__.__name__
        self.start_time = 0.0

    @logger.catch(reraise=False)
    def setup_logger(self):
        """
        Configura il logger in base a `Config.logger`.
        """

        if hasattr(self, "logger"):
            return

        logger_cfg = self.config.logger
        logging_level = getattr(logging, logger_cfg.level.upper(), "INFO")
        log_name = logger_cfg.filename or self.name

        # Configurazione di base del logger
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            level=logging_level,
        )

        self.logger = LoggerFactory.create_logger(
            log_identifier=log_name, logger_name=log_name, level=logging_level
        )
        self.logger.info(
            f"[{self.name}] Logger configurato a livello: {logger_cfg.level}"
        )

    @logger.catch(reraise=False)
    def validate_config(self):
        """
        Esegue la validazione della configurazione.
        """

        self.Config.validate()
        self.logger.debug(f"[{self.name}] Configurazione validata: {self.Config}")

    def run_agent(self):
        """
        Logica di avvio comune: prepara logger, valida config, gestisce eccezioni, etc.
        """

        self.setup_logger()
        self.validate_config()

        self.logger.info(f"[{self.name}] Avvio dell'esecuzione...")
        self.start_time = time.time()

        try:
            self.execute()
        except Exception as ex:
            self.logger.exception(f"[{self.name}] Errore durante l'esecuzione: {ex}")
        finally:
            elapsed = time.time() - self.start_time
            self.logger.info(
                f"[{self.name}] Esecuzione terminata in {elapsed:.2f} secondi"
            )

    @abstractmethod
    def execute(self):
        """
        Metodo astratto da implementare nelle classi derivate:
        la logica del “lavoro” effettivo.
        """
        pass

    @abstractmethod
    def stop(self):
        """
        Metodo astratto da implementare nelle classi derivate:
        richiesta di stop dell'agente.
        """
        pass


class BaseThreadAgent(AbstractBaseAgent, threading.Thread):
    """
    Agente base che utilizza un thread per l'esecuzione.
    """

    def __init__(self, name: str | None = None, *args, **kwargs):
        # Inizializzo il thread
        threading.Thread.__init__(self, name=name)

        # Inizializzo la parte AbstractBaseAgent
        AbstractBaseAgent.__init__(self, name)

        self._stop_event = threading.Event()

    def run(self):
        """
        Override del metodo `run` di threading.Thread: richiama la logica comune `run_agent`.
        """
        self.run_agent()

    def stop(self):
        """
        Facoltativo: set di un event per richiedere lo stop esterno del thread.
        """
        self._stop_event.set()
        self.logger.info(f"[{self.name}] Richiesta di stop ricevuta.")


class BaseProcessAgent(AbstractBaseAgent, multiprocessing.Process):
    """
    Agente base che utilizza un processo per l'esecuzione.
    """

    def __init__(self, name: str | None = None, *args, **kwargs):

        # Inizializzo il process
        multiprocessing.Process.__init__(self, name=name)

        # Inizializzo la parte AbstractBaseAgent
        AbstractBaseAgent.__init__(self, name, *args, **kwargs)

        self._stop_event = multiprocessing.Event()

    def run(self):
        """
        Override del metodo `run` di multiprocessing.Process: richiama la logica comune `run_agent`.
        """
        self.run_agent()

    def stop(self):
        """
        Facoltativo: set di un event per richiedere lo stop esterno del processo.
        """
        self._stop_event.set()
