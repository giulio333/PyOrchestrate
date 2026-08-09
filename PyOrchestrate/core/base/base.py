import inspect
import logging
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, List, final

from PyOrchestrate.utilities.logguru import LoggerFactory
from PyOrchestrate.core.base.utilities import LoggerConfig
from PyOrchestrate.core.utilities.validation import (
    ValidationResult,
    ValidationPolicy,
    ConfigValidationError,
    ConfigValidationWarning,
)

# Deep enough for a config holding a config holding a value, and a hard stop
# for anything self-referential.
_MAX_SERIALIZATION_DEPTH = 5


def _is_setting(value: Any) -> bool:
    """
    Tell a configuration value from something merely defined on the class.

    Methods, descriptors and nested classes live in the same `__dict__` as the
    settings and are not part of the configuration.
    """
    if inspect.isroutine(value) or inspect.isclass(value):
        return False
    return not isinstance(value, (classmethod, staticmethod, property))


def _as_serializable(value: Any, depth: int = 0) -> Any:
    """
    Render a configuration value in a form `json.dumps` can handle.

    `to_dict()` is sent over ZeroMQ to the CLI and serialized into the web
    interface's JSON, so a value it cannot encode fails the whole `ps` response,
    not just its own field.

    Args:
        value: Configuration value to render.
        depth: Current nesting level, to stop on a self-referential value.

    Returns:
        A JSON-encodable rendering of `value`, falling back to `str()`.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value

    if isinstance(value, Enum):
        return _as_serializable(value.value, depth + 1)

    if depth >= _MAX_SERIALIZATION_DEPTH:
        return str(value)

    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _as_serializable(item, depth + 1)
            for key, item in asdict(value).items()
        }

    if isinstance(value, dict):
        return {
            str(key): _as_serializable(item, depth + 1) for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set, frozenset)):
        return [_as_serializable(item, depth + 1) for item in value]

    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        try:
            return _as_serializable(to_dict(), depth + 1)
        except Exception:
            return str(value)

    # A plain settings object, such as ValidationPolicy: its public attributes
    # say more than the default repr, which is only a memory address.
    attributes = getattr(value, "__dict__", None)
    if attributes:
        public = {
            key: _as_serializable(item, depth + 1)
            for key, item in attributes.items()
            if not key.startswith("_")
        }
        if public:
            return public

    return str(value)


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

    def to_dict(self) -> dict:
        """
        Convert the configuration to a dictionary.

        Notes:
            The result is built in the order attributes actually resolve:
            inherited class defaults first, then the ones the leaf class
            overrides, then instance attributes, then the user-defined values
            passed to the constructor.

            Reading only `self.__class__.__dict__` left out every inherited
            default, and skipping every underscore key left out the contents of
            `_custom_attr` — the user-defined settings `__getattribute__` goes
            out of its way to expose. `pyorchestrate ps` and `GET /api/agents`
            print this, and reported neither.

            Values are rendered JSON-encodable, because that is what both
            consumers do with them.

        Returns:
            dict: Dictionary representation of the configuration.
        """
        result: dict[str, Any] = {}

        # Reversed MRO, so a subclass default overrides the base one.
        for klass in reversed(type(self).__mro__):
            for key, value in vars(klass).items():
                if not key.startswith("_") and _is_setting(value):
                    result[key] = value

        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                result[key] = value

        # Constructor kwargs win over everything, as they do on attribute access.
        result.update(self._custom_attr)

        return {key: _as_serializable(value) for key, value in result.items()}

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

    This class automatically handles plugin attributes defined as class attributes
    and allows overriding them via constructor kwargs, eliminating the need for
    explicit __init__ implementations in derived classes.

    Example:
        ```python
        class MyPlugin(BaseClassPlugin):
            # Define default plugins as class attributes
            zmq: ZeroMQPubSub = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
            heartbeat: HeartbeatPlugin | None = None

        # Use defaults
        plugin1 = MyPlugin()

        # Override specific plugins
        plugin2 = MyPlugin(heartbeat=HeartbeatPlugin())
        ```
    """

    def __init__(
        self,
        **kwargs,
    ):
        # Store user-defined attributes passed via constructor
        # These will override class-level default values
        self._custom_attr: dict[str, Any] = kwargs

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
            plugin (BaseClassPlugin): Plugin instance to be used.
            name (str | None): Identifier used for logging. Defaults to class name if None.
            **kwargs: Additional attributes to set on the instance.

        Note:
            All kwargs are set as instance attributes directly.
        """
        # self.config = config if config else self.Config()
        # self.plugin = plugin if plugin else self.Plugin()
        # self.name = name if name else self.__class__.__name__

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

    @final
    def validate_config(self):
        """
        @final

        Validates the configuration.

        Notes:
            This method is called during initialization to validate the configuration.
            If the configuration is invalid, a `ConfigValidationError` is raised.
            If the configuration has warnings, a `ConfigValidationWarning` is raised.

        Warning:
            Do not override this method. If you need to implement custom validation logic,
            override the `validate` method in the `Config` class.

        Raises:
            ConfigValidationError: If the configuration is invalid.
            ConfigValidationWarning: If the configuration has warnings.
        """
        try:
            self.config._validate()
        except ConfigValidationError as e:
            self.logger.error(e)
            raise e
        except ConfigValidationWarning as w:
            self.logger.warning(w)
        self.logger.debug(f"Self configuration validated.")

    def __getattr__(self, key: str) -> Any:
        try:
            custom_attr = object.__getattribute__(self, "_custom_attr")
        except AttributeError:
            custom_attr = {}
        if key in custom_attr:
            return custom_attr[key]
        return object.__getattribute__(self, key)
