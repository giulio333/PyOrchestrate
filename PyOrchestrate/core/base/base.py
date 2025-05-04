import logging
from typing import Any, List

from PyOrchestrate.utilities.logguru import LoggerFactory
from PyOrchestrate.core.base.utilities import LoggerConfig
from PyOrchestrate.core.utilities.validation import (
    ValidationResult,
    ValidationPolicy,
    ConfigValidationError,
    ConfigValidationWarning,
)


class BaseClassConfig:
    """
    Base class for configuration settings.

    Attributes:
        logger_config (LoggerConfig): Configuration for the logger component.
        validation_policy (ValidationPolicy): Policy for managing validation.

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
    validation_policy: ValidationPolicy = ValidationPolicy()

    def __init__(
        self,
        logger_config: LoggerConfig | None = None,
        validation_policy: ValidationPolicy | None = None,
        **kwargs,
    ):
        if logger_config is not None:
            self.logger_config = logger_config

        if validation_policy is not None:
            self.validation_policy = validation_policy

        # store user-defined attributes
        self._custom_attr: dict[str, Any] = kwargs

    def _validate(self):
        """
        Validates the configuration settings.

        This method performs configuration validation and raises ConfigValidationError if
        validation fails based on the configured ValidationPolicy.

        Returns:
            List[ValidationResult]: List of validation results.

        Raises:
            ConfigValidationError: If the configuration is invalid and policy requires it.
            ConfigValidationWarning: If the configuration has warnings and policy requires it.
        """
        results = self.validate()

        # Filter out invalid results
        invalid_results = [r for r in results if not r.is_valid]

        if invalid_results:
            raise_type = self.validation_policy.should_raise(invalid_results)
            if raise_type == "error":
                raise ConfigValidationError(
                    "Validation failed",
                    invalid_results,
                    config_class=self.__class__.__name__,
                )
            elif raise_type == "warning":
                raise ConfigValidationWarning(
                    "Validation warnings",
                    invalid_results,
                    config_class=self.__class__.__name__,
                )

        return results

    def validate(self) -> List[ValidationResult]:
        """
        Override this method to implement custom validation logic in derived classes.

        Returns:
            List[ValidationResult]: List of validation results.
        """
        return []

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
    """
    Base class for plugins.

    Can be used to store Plugin objects.
    """

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

    def __init__(
        self,
        config: BaseClassConfig | None = None,
        plugin: BaseClassPlugin | None = None,
        name: str | None = None,
        **kwargs,
    ):
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
        self.config = config if config else self.Config()
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
