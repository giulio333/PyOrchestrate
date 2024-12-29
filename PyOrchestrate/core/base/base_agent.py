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
    """

    def __init__(self, name: str | None, config: T, **kwargs):
        super().__init__(name=name, config=config, **kwargs)
        self._stop_event = None

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

        This method is called by the `run` method of the derived classes. So it can be considered the entry point for
        the agent execution.
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
        pass

    @abstractmethod
    def stop(self):
        """
        Event set to request the external stop of the process.
        """
        pass

    @abstractmethod
    def _info(self):
        pass


class ThreadAgent(BaseAgent[T], threading.Thread):
    """
    Agent class based on threading.Thread.

    This class is a base class for all agents that need to run in a separate thread. It provides a common interface for
    the agent's lifecycle management.
    """

    def __init__(self, config: T, name: str | None = None, **kwargs):
        threading.Thread.__init__(self, name=name)
        BaseAgent.__init__(self, name=name, config=config, **kwargs)

        self._stop_event = threading.Event()  # type: ignore

    def run(self):
        """
        Override of the `run` method of threading.Thread: it calls the common logic `run_agent`.
        """
        self.run_agent()

    def stop(self):
        """
        Event set to request the external stop of the process.
        """
        self._stop_event.set()

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent execution logic.
        """
        pass

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
        BaseAgent.__init__(self, name=name, config=config, **kwargs)

        self._stop_event = multiprocessing.Event()  # type: ignore

    def run(self):
        """
        Override of the `run` method of multiprocessing.Process: it calls the common logic `run_agent`.
        """
        self.run_agent()

    def stop(self):
        """
        Event set to request the external stop of the process.
        """
        self._stop_event.set()

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent execution logic.
        """
        pass

    def _info(self):
        super()._info()
