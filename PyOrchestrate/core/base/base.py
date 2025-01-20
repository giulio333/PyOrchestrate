import logging
from typing import Generic, TypeVar, Type

from PyOrchestrate.utilities.logguru import LoggerFactory
from ..base.utilities import LoggerConfig


class BaseAgentConfig:
    """
    BaseClass configuration class.

    Attributes:
        logger_config (LoggerConfig): Logger configuration.

    Notes:
        Class attributes store default values for the configuration parameters. If you want to change the default
        values, you can override them in the derived class or pass them as arguments to the constructor.

        User-defined attributes follow the same pattern. They can be passed as arguments to the constructor or
        overridden in the derived class.

    Examples:
        You can create a custom configuration class by inheriting from the BaseClass.Config class and overriding the
        desired attributes.

        >>> class Config(BaseClass.Config):
        ...     logger = LoggerConfig(level="DEBUG")
        >>> default_config = Config()
        >>> custom_config = Config(logger=LoggerConfig(level="INFO"))
    """

    logger_config: LoggerConfig = LoggerConfig()

    def __init__(self, logger_config: LoggerConfig | None = None, **kwargs):
        if logger_config is not None:
            self.logger_config = logger_config

        # store user-defined attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def validate(self):
        """
        Validates certain conditions related to the class. This method is intended to
        ensure the integrity or correctness of parameters or
        state and can be overridden in subclasses to customize validation logic.
        """
        pass

    def __str__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"


T = TypeVar("T", bound="BaseAgentConfig")


class BaseClass(Generic[T]):
    """
    Base class for all classes.

    Every class has a logger and a configuration object.
    """

    Config = BaseAgentConfig

    start_time: float

    def __init__(self, config: T, name: str | None = None, **kwargs):
        self.config = config
        self.name = name if name else self.__class__.__name__

        for key, value in kwargs.items():
            setattr(self, key, value)

    def setup_logger(self):
        """
        Set up the logger.

        Notes:
            Logger configuration is read from the `config.logger` attribute.
        """

        if hasattr(self, "logger"):
            return

        logger_cfg = self.config.logger_config
        logging_level = getattr(logging, logger_cfg.level.upper(), "DEBUG")
        log_name = logger_cfg.filename or self.name

        self.logger = LoggerFactory.create_logger(
            log_identifier=log_name, logger_name=log_name, level=logging_level
        )
