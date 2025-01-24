"""
BaseAgent module.
"""

import threading
import multiprocessing
import time
from abc import ABC
from typing import final, TypeVar, Protocol

from .base import BaseClass


class BaseAgentConfig(BaseClass.Config):
    """
    Base agent configuration class.

    Attributes:
        logger_config (LoggerConfig): Logger configuration.

    Notes:
        Class attributes store default values for the configuration parameters. If you want to change the default
        values, you can override them in the derived class or pass them as arguments to the constructor.

        User-defined attributes follow the same pattern. They can be passed as arguments to the constructor or
        overridden in the derived class.

    Examples:
        You can create a custom configuration class by inheriting from the BaseAgent.Config class and overriding the
        desired attributes.

        >>> class Config(BaseClass.Config):
        ...     value = "value"
        >>> default_config = Config()
        >>> custom_config = Config(value="new value")
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

    This class provides a common interface for the agent's lifecycle management. It defines the main methods that an
    agent must implement to be executed correctly.

    Every agent has a set of events to manage the internal state and the external commands. The `state_events` attribute
    contains the events related to the internal state of the agent, while the `control_events` attribute contains the
    events related to external commands.

    Warnings:
        Always call the parent method when overriding a method (use super()).

    Notes:
        Derived classes must implement the `execute` method to define the agent's logic. You can also implement the
        `setup` method to initialize some agent attributes before the cycle method.

    Attributes:
        state_events (StateEvents): Events related to the internal state of the agent.
        control_events (ControlEvents): Events related to external commands.

    Methods:
        run: Main method to run the agent.
        setup: Method called when the agent is started to perform the setup.
        execute: Method called to execute the agent logic.
        stop: Method to request the external stop of the agent.
        validate_config: Validate the configuration.
        on_stop: Method called when the agent is stopped.
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
        a_type: str,
        control_events: ControlEvents,
        state_events: StateEvents,
        **kwargs,
    ):
        """
        BaseAgent constructor.

        Args:
            name: The agent name.
            config: The agent configuration.
            a_type: The agent type.
            control_events: Events related to external commands.
            state_events: Events related to the internal state of the agent.
        """
        super().__init__(name=name, config=config, **kwargs)

        self.state_events = state_events
        """Events related to the internal state of the agent."""
        self.control_events = control_events
        """Events related to external commands."""
        self.a_type = a_type

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

        Method called when the agent is started to perform the setup.

        Warnings:
            Make sure to call the parent method if you override it.

        Notes:
            Here you can implement the setup logic. This method is called once before the agent `execute` method.

            You can control this phase using the `control_events.setup_event` event.

            When the setup is completed, the agent emits the `state_events.ready_event` event.
        """
        if self.control_events is not None:
            self.control_events.setup_event.wait()

    def execute(self):
        """
        @template

        Method called to execute the agent logic.

        Warnings:
            Make sure to call the parent method if you override it.
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
        Validate the configuration.

        You can override this method to add custom validation logic.

        Raises:
            ValidationError: If the configuration is not valid.
        """

        try:
            self.config.validate()
        except Exception as ex:
            self.logger.error(f"Configuration validation failed: {ex}")
            raise ValidationError(str(ex))

        self.logger.debug(f"Self configuration validated.")

    def on_stop(self):
        """
        @optional

        Method called when the agent is stopped.

        Notes:
            This method can be overridden in the derived class to implement custom logic to be executed when the agent
            is stopped.
        """
        pass

    def on_close(self):
        """
        @optional

        Method called when the agent is closing.

        Notes:
            This method can be overridden in the derived class to implement custom logic to be executed when the agent
            is closing.
        """
        pass

    def _info(self) -> None:
        """
        @template

        Log the agent configurations.

        Returns:
            None
        """
        self.logger.debug(f"Config: logger_level: {self.config.logger_config.level}")


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
    Protocol that defines the methods and attributes required for an agent.
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
