"""
BaseAgent module.
"""

import threading
import multiprocessing
import time
from abc import ABC, abstractmethod
from typing import final, TypeVar, Protocol, Literal, List, Dict, Type

from ..base.base import BaseClass
from ..plugins.plugin_protocols import Plugin


class BaseAgentConfig(BaseClass.Config):
    """
    Base agent configuration class.

    Class attributes store default values for configuration parameters. These values can be
    overridden either in derived classes or through constructor arguments.

    User-defined attributes follow the same pattern, they can be set via constructor
    arguments or overridden in derived classes.

    Attributes:
        logger_config (LoggerConfig): Configuration for the logger.

    Examples:
        Creating a custom configuration for a ChatAgent:

        >>> class ChatAgentConfig(BaseAgent.Config):
        ...     model_name = "gpt-3.5-turbo"  # Default model name
        ...     max_tokens = 1000             # Default maximum tokens per request
        ...     temperature = 0.7             # Default temperature for sampling

        >>> # Default configuration
        >>> default_chat_config = ChatAgentConfig()

        >>> # Custom configuration
        >>> custom_chat_config = ChatAgentConfig(
        ...     model_name="gpt-4",
        ...     max_tokens=2000,
        ...     temperature=0.9
        ... )
    """


T = TypeVar("T", bound=BaseAgentConfig)


class ValidationError(Exception):
    """
    Exception raised for errors in the configuration validation.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class BaseAgent(BaseClass[T], ABC):
    """
    Abstract base class for all agents.

    This class provides a common interface for agent lifecycle management, defining
    the essential methods that an agent must implement.

    Each agent manages two types of events:

    - state_events: For managing the agent's internal state
    - control_events: For handling external commands

    Warnings:
        When overriding methods, always call the parent implementation using super().

    Usage:
        Derived classes must implement the `execute` method to define their core logic.
        The `setup` method can be optionally overridden to perform initialization
        before the execution begins.

    Attributes:
        state_events (StateEvents): Events for internal state management.
        control_events (ControlEvents): Events for external command handling.
        plugins (Dict[str, Plugin]): Registered plugins.

    Methods:
        run: Main entry point for agent execution.
        setup: Performs initialization when the agent starts.
        execute: Implements the agent's core logic.
        stop: Requests external termination of the agent.
        validate_config: Validates the configuration.
        on_stop: Handles cleanup when the agent is stopped.
        register_plugin: Registers a plugin.
        unregister_plugin: Unregisters a plugin.
        get_plugin: Retrieves a registered plugin.
    """

    a_type: str = ""

    Config = BaseAgentConfig

    class StateEvents:
        """
        Events related to the internal state of the agent.

        Attributes:
            ready_event: Event to signal that the agent is ready to start the execution.
            close_event: Event to signal that the agent has completed the execution.
        """

        def __init__(self, ready_event, close_event):
            self.ready_event = ready_event
            self.close_event = close_event

    class ControlEvents:
        """
        Events related to external commands.

        Attributes:
            setup_event: Event to signal that the agent can make the setup.
            execute_event: Event to signal that the agent can make the execution.
            stop_event: Event to signal that the agent must stop.
        """

        def __init__(self, setup_event, execute_event, stop_event):
            self.setup_event = setup_event
            self.execute_event = execute_event
            self.stop_event = stop_event

    def __init__(
        self,
        name: str | None,
        config: T,
        a_type: Literal["process", "thread"],
        control_events: ControlEvents,
        state_events: StateEvents,
        **kwargs,
    ):
        """
        Creates an agent with the specified configuration and event handlers. The agent can be
        identified by its name in logs and uses events to manage its lifecycle and respond to
        external commands. The agent type determines whether it will run as a process or thread.

        The agent's behavior is defined by two types of events:

        - State events track the agent's internal state transitions
        - Control events handle external commands and execution flow

        Additional keyword arguments are automatically stored as instance attributes,
        allowing for flexible extension of the agent's properties.

        Args:
            name (str | None): A unique identifier for the agent used in logging
            config (T): Configuration parameters that define the agent's behavior
            a_type (Literal["process", "thread"]): Determines if agent runs as process or thread
            control_events (ControlEvents): Signals for external command handling
            state_events (StateEvents): Signals for internal state management
        """
        super().__init__(name=name, config=config, **kwargs)

        self.state_events = state_events
        """Events related to the internal state of the agent."""
        self.control_events = control_events
        """Events related to external commands."""
        self.a_type = a_type
        """The agent type (process or thread)."""
        self.plugins: Dict[str, Plugin] = {}
        """Registered plugins."""

    @final
    def run(self):
        """
        Main method to run the agent.

        Warnings:
            Do not override this method. If you need to implement custom logic when the agent is started, you can
            override the `setup` and `execute` methods.

        Notes:
            This method is called by the `run` method of the derived classes. So it can be considered the entry point
            for the agent execution.
        """
        self.start_time = time.time()

        self.setup_logger()

        try:
            self._info()

            self.validate_config()

            self.setup()

            self.logger.info("Starting...")

            if self.state_events is not None:
                self.state_events.ready_event.set()

            self.execute()

        except Exception as ex:
            self.logger.exception(f"[{self.name}] Error during execution: {ex}")

        finally:

            self.logger.info("Execution completed.")

            self.on_close()

            if self.state_events is not None:
                self.state_events.close_event.set()

            elapsed = time.time() - self.start_time
            self.logger.debug(f"Agent lifecycle completed in {elapsed:.3f} seconds.")

    def setup(self):
        """
        @template
        Performs initialization when the agent starts.

        Warnings:
            When overriding, ensure to call the parent implementation.

        Notes:
            Implement setup logic here. This method runs once before `execute`.

            - Uses `control_events.setup_event` for execution control.
            - Triggers `state_events.ready_event` upon completion.
        """
        if self.control_events is not None:
            self.control_events.setup_event.wait()

    def execute(self):
        """
        @template
        Implements the agent's core logic.

        Warnings:
            When overriding, ensure to call the parent implementation.
        """
        if self.control_events is not None:
            self.control_events.execute_event.wait()

    @final
    def stop(self):
        """
        Method to request the external stop of the agent.

        Notes:
            If you need to implement custom logic when the agent is being stopped, you can override the `on_stop` method.

        Warnings:
            Do not override this method.
        """
        self.on_stop()
        self.control_events.stop_event.set()

    def validate_config(self):
        """
        @template
        Validates the agent configuration.

        Override this method to implement custom validation logic.

        Raises:
            ValidationError: If the configuration is invalid.
        """

        try:
            self.config.validate()
        except Exception as ex:
            self.logger.error(f"Configuration validation failed: {ex}")
            raise ValidationError(str(ex))

        self.logger.debug(f"Self configuration validated.")

    def on_stop(self):
        """
        Handles cleanup when the agent is stopped.

        Notes:
            Override this method to implement custom cleanup logic
            that should execute when the agent is stopped.
        """
        pass

    def on_close(self):
        """
        Performs final cleanup when the agent is closing.

        Notes:
            Override this method to implement custom cleanup logic
            that should execute during agent shutdown.
        """
        pass

    def _info(self) -> None:
        """
        Logs the agent configuration details.

        Returns:
            None
        """
        self.logger.debug(f"Config: logger_level: {self.config.logger_config.level}")

    def register_plugin(self, plugin: Plugin):
        """
        Registers a plugin.

        Args:
            plugin (Plugin): The plugin to register.
        """
        plugin_name = plugin.__class__.__name__
        self.plugins[plugin_name] = plugin
        plugin.initialize()
        self.logger.info(f"Plugin '{plugin_name}' registered.")

    def unregister_plugin(self, plugin_name: str):
        """
        Unregisters a plugin.

        Args:
            plugin_name (str): The name of the plugin to unregister.
        """
        if plugin_name in self.plugins:
            plugin = self.plugins.pop(plugin_name)
            plugin.finalize()
            self.logger.info(f"Plugin '{plugin_name}' unregistered.")

    def get_plugin(self, plugin_name: str) -> Plugin:
        """
        Retrieves a registered plugin.

        Args:
            plugin_name (str): The name of the plugin to retrieve.

        Returns:
            Plugin: The registered plugin.

        Raises:
            KeyError: If the plugin is not found.
        """
        if plugin_name not in self.plugins:
            raise KeyError(f"Plugin '{plugin_name}' not found.")

        return self.plugins[plugin_name]


class BaseProcessAgent(BaseAgent[T], multiprocessing.Process, ABC):
    a_type: str = "process"

    def __init__(self, name: str | None, config: T, **kwargs):
        """
        BaseProcessAgent constructor.

        Args:
            name: The agent name.
            config: The agent configuration.
        """
        multiprocessing.Process.__init__(self, name=name)
        BaseAgent.__init__(self, name=name, config=config, a_type="process", **kwargs)


class BaseThreadAgent(BaseAgent[T], threading.Thread, ABC):
    a_type: str = "thread"

    def __init__(self, name: str | None, config: T, **kwargs):
        """
        BaseThreadAgent constructor.

        Args:
            name: The agent name.
            config: The agent configuration.
        """
        threading.Thread.__init__(self, name=name)
        BaseAgent.__init__(self, name=name, config=config, a_type="thread", **kwargs)


class AgentProtocol(Protocol):
    """
    Protocol defining the required interface for agent implementations.

    This protocol specifies the methods and attributes that any agent
    implementation must provide.
    """

    a_type: str
    name: str
    daemon: bool
    ident: int | None
    pid: int | None

    def run(self) -> None: ...

    def setup(self) -> None: ...

    def execute(self) -> None: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def join(self) -> None: ...

    def is_alive(self) -> bool: ...

    def validate_config(self) -> None: ...

    def on_stop(self) -> None: ...
