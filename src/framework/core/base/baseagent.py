import threading
import multiprocessing
import time
import logging
from abc import ABC, abstractmethod
from loguru import logger
from dataclasses import dataclass

from ...utilities.logguru import LoggerFactory
from ..base.utilities import LoggerConfig


class BaseConfig(ABC):
    """
    Base configuration class.
    """

    logger: LoggerConfig = LoggerConfig()

    @classmethod
    def validate(cls):
        """
        Validate the configuration.
        """
        pass


class AbstractBaseAgent(ABC):
    """
    Abstract base class for all agents.
    """
    start_time: float

    @dataclass
    class Config(BaseConfig):
        """
        Agent configuration class.

        Attributes:
            logger (LoggerConfig): Logger configuration.
        """

    def __init__(self, name: str | None = None, config: BaseConfig | None = None, *args, **kwargs):

        self.logger = None
        self.config = config if config else self.Config()
        self.name = name if name else self.__class__.__name__

    @logger.catch(reraise=False)
    def setup_logger(self):
        """
        Set up the logger.

        Notes:
            Logger configuration is read from the `config.logger` attribute.
        """

        if self.logger is not None:
            return

        logger_cfg = self.config.logger
        logging_level = getattr(logging, logger_cfg.level.upper(), "INFO")
        log_name = logger_cfg.filename or self.name

        self.logger = LoggerFactory.create_logger(
            log_identifier=log_name, logger_name=log_name, level=logging_level
        )
        self.logger.debug("Logger initialized.")

    @logger.catch(reraise=False)
    def validate_config(self):
        """
        Validate the configuration.
        """

        self.config.validate()
        self.logger.info("Configuration successfully validated.")

    def run_agent(self):

        self.setup_logger()
        self.validate_config()

        self.logger.info("Starting agent...")

        self.start_time = time.time()

        try:
            self.execute()
        except Exception as ex:
            self.logger.exception(f"[{self.name}] Errore durante l'esecuzione: {ex}")
        finally:
            elapsed = time.time() - self.start_time
            self.logger.info(
                f"execution completed in {elapsed:.3f} seconds."
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

    def __init__(self, name: str | None = None, *args, **kwargs):
        threading.Thread.__init__(self, name=name)
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

    def __init__(self, name: str | None = None, *args, **kwargs):
        multiprocessing.Process.__init__(self, name=name)
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
