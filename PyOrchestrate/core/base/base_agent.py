"""
BaseAgent module.
"""

import threading
import multiprocessing
import time
from abc import ABC, abstractmethod
from time import sleep
from typing import final, TypeVar

from .base import BaseClass

T = TypeVar("T", bound="BaseClass.Config")


class BaseAgent(BaseClass[T], ABC):
    """
    Abstract base class for all agents.
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

    def __init__(self, name: str | None, config: T, **kwargs):
        super().__init__(name=name, config=config, **kwargs)
        self._stop_event = None
        self.ready_event = None

    def validate_config(self):
        """
        Validate the configuration.
        """
        self.config.validate()
        self.logger.debug(f"Self configuration validated.")

    @final
    def run_agent(self):
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

            self.logger.info("Starting...")

            self.execute()
        except Exception as ex:
            self.logger.exception(f"[{self.name}] Errore durante l'esecuzione: {ex}")
        finally:
            elapsed = time.time() - self.start_time
            self.logger.info(f"execution completed in {elapsed:.3f} seconds.")

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent specific execution logic.
        """
        self.setup()

    @abstractmethod
    def stop(self):
        """
        Event set to request the external stop of the process.
        """
        self.on_stop()

    @abstractmethod
    def setup(self):
        """
        Method called when the agent is started to perform the setup.

        Warnings:
            Make sure to call the parent method if you override it.

        Notes:
            Here you can implement the setup logic. This method is called once before the Agent cycle method.
        """
        pass

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

    Notes:


    Attributes:
        _stop_event (threading.Event): Event to request the external stop of the process.

    Methods:
        run: Override of the `run` method of threading.Thread: it calls the common logic `run_agent`.
        stop: Event set to request the external stop of the process.
        execute: Abstract method to be implemented in derived classes: Agent execution logic.
        _info: Print the agent information.
    """

    def __init__(self, config: T, name: str | None = None, ready_event=None, **kwargs):
        threading.Thread.__init__(self, name=name)
        BaseAgent.__init__(self, name=name, config=config, **kwargs)

        self._stop_event = threading.Event()  # type: ignore
        self.ready_event = ready_event

    @final
    def start(self):
        """
        Start current agent.
        """
        super().start()

    @final
    def run(self):
        """
        Override of the `run` method of threading.Thread: it calls the common logic `run_agent`.
        """
        self.run_agent()

    @final
    def stop(self):
        """
        Event set to request the external stop of the thread.

        Warning:
            Do not override this method. If you need to implement custom logic when the agent is stopped, you can
            override the `on_stop` method.
        """
        super().stop()
        self._stop_event.set()

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent execution logic.
        """
        super().execute()
        self.ready_event.set()

    def _info(self):
        super()._info()


class ProcessAgent(BaseAgent[T], multiprocessing.Process):
    """
    Agent class based on multiprocessing.Process.

    This class is a base class for all agents that need to run in a separate process. It provides a common interface for
    the agent's lifecycle management.
    """

    def __init__(self, config: T, name: str | None = None, ready_event=None, **kwargs):
        multiprocessing.Process.__init__(self, name=name)
        BaseAgent.__init__(self, name=name, config=config, **kwargs)

        self._stop_event = multiprocessing.Event()  # type: ignore
        self.ready_event = ready_event

    @final
    def start(self):
        """
        Start current process agent.

        Notes:
            Internally, it calls the `run` method of the Process class.
        """
        super().start()

    @final
    def run(self):
        """
        Override of the `run` method of multiprocessing.Process.
        """
        self.run_agent()

    def stop(self):
        """
        Event set to request the external stop of the process.

        Warning:
            Do not override this method. If you need to implement custom logic when the agent is stopped, you can
            override the `on_stop` method.
        """
        super().stop()
        self._stop_event.set()

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent execution logic.
        """
        super().execute()
        self.ready_event.set()

    def _info(self):
        super()._info()
