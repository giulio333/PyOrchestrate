"""
BaseAgent module.
"""

import threading
import multiprocessing
import time
from abc import ABC, abstractmethod
from typing import final, TypeVar

from .base import BaseClass

T = TypeVar("T", bound="BaseClass.Config")


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
        stop: Event set to request the external stop of the process.
        setup: Method called when the agent is started to perform the setup.
        on_stop: Method called when the agent is stopped.
        _info: Print the agent information.
    """

    class Config(BaseClass.Config):
        """
        Base agent configuration class.

        Attributes:
            logger (LoggerConfig): Logger configuration.

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

    def __init__(self, name: str | None, config: T, a_type: str, control_events: ControlEvents,
                 state_events: StateEvents, **kwargs):
        """
        BaseAgent constructor.

        Args:
            name: The agent name.
            config: The agent configuration.
            a_type: The agent type.
            emit_setup: Event to signal that the agent can make the setup.
            emit_execution: Event to signal that the agent can make the execution.
        """
        super().__init__(name=name, config=config, **kwargs)

        self.state_events = state_events
        """Events related to the internal state of the agent."""
        self.control_events = control_events
        """Events related to external commands."""

    def validate_config(self):
        """
        Validate the configuration.
        """
        self.config.validate()
        self.logger.debug(f"Self configuration validated.")

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

            self.state_events.ready_event.set()

            self.execute()
        except Exception as ex:
            self.logger.exception(f"[{self.name}] Errore durante l'esecuzione: {ex}")
        finally:
            self.state_events.close_event.set()
            elapsed = time.time() - self.start_time
            self.logger.info(f"execution completed in {elapsed:.3f} seconds.")

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent specific execution logic.
        """
        self.control_events.execute_event.wait()

    @final
    def stop(self):
        """
        Event set to request the external stop of the thread.

        Warning:
            Do not override this method. If you need to implement custom logic when the agent is stopped, you can
            override the `on_stop` method.
        """
        self.control_events.stop_event.set()

    @abstractmethod
    def setup(self):
        """
        Method called when the agent is started to perform the setup.

        Warnings:
            Make sure to call the parent method if you override it.

        Notes:
            Here you can implement the setup logic. This method is called once before the agent `execute` method.

            You can control this phase using the `setup_event` attribute of the `control_events` object.

            When the setup is completed, the agent emits the `ready_event` event of the `state_events` object.
        """
        self.control_events.setup_event.wait()

    def on_stop(self):
        """
        Method called when the agent is stopped.

        Notes:
            This method can be overridden in the derived class to implement custom logic to be executed when the agent
            is stopped.
        """
        pass

    @abstractmethod
    def _info(self):
        pass


class ThreadAgent(BaseAgent[T], threading.Thread):
    """
    ThreadAgent base on BaseAgent and threading.Thread.

    This class is a base class for all agents that need to run in a separate thread. It provides a common interface for
    the agent's lifecycle management.

    Methods:
        run: Override of the `run` method of threading.Thread: it calls the common logic `run_agent`.
        stop: Event set to request the external stop of the process.
        execute: Abstract method to be implemented in derived classes: Agent execution logic.
        _info: Print the agent information.
    """

    def __init__(self, config: T, name: str | None = None, **kwargs):
        threading.Thread.__init__(self, name=name)
        BaseAgent.__init__(self, name=name, config=config, a_type="thread", **kwargs)

    @final
    def start(self):
        """
        Start current process agent.

        Notes:
            Internally, it calls the `run` method of the agent in a new thread.

        Returns:
            None
        """
        super().start()

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent execution logic.
        """
        super().execute()
        # self.control_events.execute_event.set()

    def _info(self):
        super()._info()


class ProcessAgent(BaseAgent[T], multiprocessing.Process):
    """
    Agent class based on multiprocessing.Process.

    This class is a base class for all agents that need to run in a separate process. It provides a common interface for
    the agent's lifecycle management.
    """

    def __init__(self, config: T, name: str | None = None, **kwargs):
        multiprocessing.Process.__init__(self, name=name)
        BaseAgent.__init__(self, name=name, config=config, a_type="process", **kwargs)

    @final
    def start(self):
        """
        Start current process agent.

        Notes:
            Internally, it calls the `run` method of the agent in a new process.

        Returns:
            None
        """
        super().start()

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent execution logic.
        """
        super().execute()
        # self.events.ready_event.set()

    def _info(self):
        super()._info()
