import threading
import multiprocessing
import time
import logging
from abc import ABC, abstractmethod
from loguru import logger
from dataclasses import dataclass, field

from ...utilities.logguru import LoggerFactory
from ..base.utilities import LoggerConfig


@dataclass
class BaseConfig(ABC):
    """
    Base configuration class.

    Attributes:
        logger (LoggerConfig): Logger configuration.
    """

    logger: LoggerConfig = field(default_factory=LoggerConfig)

    def validate(self):
        """
        Validates certain conditions related to the class. This method is intended to
        ensure the integrity or correctness of class-level behaviors, parameters, or
        state and can be overridden in subclasses to customize validation logic.
        """
        pass


class BaseClass:
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

    @logger.catch(reraise=True)
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
        self.logger.debug(f"Logger initialized: {self.config.logger}")


class AbstractBaseAgent(BaseClass, ABC):
    """
    Abstract base class for all agents.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @logger.catch(reraise=True)
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
    def stop(self):
        """
        Abstract method to be implemented in derived classes: Agent stop logic.
        """
        pass

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent execution logic.
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

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent execution logic.
        """
        pass


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

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent execution logic.
        """
        pass
