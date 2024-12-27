import threading
import multiprocessing
import time
import logging
from abc import ABC, abstractmethod
from loguru import logger

from ...utilities.logguru import LoggerFactory
from ..base.utilities import LoggerConfig


class BaseConfig(ABC):
    """
    Base configuration class.

    All Agent's Config classes should inherit from this class.

    Attributes:
        logger (LoggerConfig): Logger configuration.
    """

    def __init__(self, logger_config: LoggerConfig | None = None):
        self.logger = logger_config if logger_config else LoggerConfig()

    def validate(self):
        """
        Validates certain conditions related to the class. This method is intended to
        ensure the integrity or correctness of parameters or
        state and can be overridden in subclasses to customize validation logic.
        """
        pass


class BaseClass:
    """
    Base class for all classes.

    Every class has a logger and a configuration object.
    """
    start_time: float

    class Config(BaseConfig):
        """
        Configuration class for the BaseClass.

        Attributes:
            logger (LoggerConfig): Logger configuration.
        """

    def __init__(self, name: str | None = None, config: BaseConfig | None = None, stop_callback=None, *args, **kwargs):
        self.logger = None
        self.config = config if config else self.Config()
        self.name = name if name else self.__class__.__name__
        self.stop_callback = stop_callback

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

