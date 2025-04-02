import logging
from typing import Any, cast

from PyOrchestrate.utilities.logguru import LoggerFactory
from PyOrchestrate.core.base.utilities import LoggerConfig


class BaseClassConfig:
    """
    Base class for configuration settings.

    Attributes:
        logger_config (LoggerConfig): Configuration for the logger component.

    Notes:
        Default configuration values are stored as class attributes. These defaults can be:
        - Overridden in derived classes
        - Modified through constructor arguments
        - Extended with additional user-defined attributes

    Examples:
        Create a custom configuration by subclassing BaseClass.Config:

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
        self._custom_attr: dict[str, Any] = kwargs

    def validate(self):
        """
        Validates the configuration settings.

        This method should be overridden in subclasses to implement specific validation logic for configuration parameters.

        Raises:
            ValueError: If the configuration is invalid.
        """
        pass

    def __getattribute__(self, key: str) -> Any:
        try:
            custom_attr = object.__getattribute__(self, "_custom_attr")
        except AttributeError:
            custom_attr = {}
        if key in custom_attr:
            return custom_attr[key]
        return object.__getattribute__(self, key)

    def __str__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"


class BaseClassPlugin:
    pass


class BaseClass:
    """
    Base class providing core functionality.

    Features:
        - Configured through a type-safe configuration object
        - Built-in logging support
        - Extensible through inheritance
    """

    Config = BaseClassConfig
    Plugin = BaseClassPlugin

    start_time: float

    def __init__(self, config, plugin, name: str | None = None, **kwargs):
        """
        Initialize a new instance.

        Args:
            config (T): Configuration object.
            plugin: Plugin instance to be used.
            name (str | None): Identifier used for logging. Defaults to class name if None.
            **kwargs: Additional attributes to set on the instance.

        Note:
            All kwargs are set as instance attributes directly.
        """
        self.config = config
        self.plugin = plugin
        self.name = name if name else self.__class__.__name__

        # store user-defined attributes
        self._custom_attr: dict[str, Any] = kwargs

    def setup_logger(self):
        """
        Initialize the logger instance.

        The logger is configured using settings from config.logger_config.
        If a logger is already set up, this method has no effect.
        """

        if hasattr(self, "logger"):
            return

        logger_cfg = self.config.logger_config
        logging_level = getattr(logging, logger_cfg.level.upper(), "DEBUG")
        log_name = logger_cfg.filename or self.name

        self.logger = LoggerFactory.create_logger(
            log_identifier=log_name, logger_name=log_name, level=logging_level
        )

    def __getattr__(self, key: str) -> Any:
        try:
            custom_attr = object.__getattribute__(self, "_custom_attr")
        except AttributeError:
            custom_attr = {}
        if key in custom_attr:
            return custom_attr[key]
        return object.__getattribute__(self, key)
