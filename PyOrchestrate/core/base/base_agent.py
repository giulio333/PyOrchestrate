import threading
import multiprocessing
import time
from abc import ABC, abstractmethod
from typing import final

from loguru import logger

from .base import BaseClass

class BaseAgent(BaseClass, ABC):
    """
    Abstract base class for all agents.
    """

    def __init__(self,name,config, *args, **kwargs):
        super().__init__(name=name, config=config,*args, **kwargs)
        self._stop_event = None

    @logger.catch(reraise=True)
    def validate_config(self):
        """
        Validate the configuration.
        """

        self.config.validate()
        self.logger.info("Configuration successfully validated.")

    @final
    def run_agent(self):
        """
        Main method to run the agent.

        This method is called by the `run` method of the derived classes. So it can be considered the entry point for
        the agent execution.
        """

        self.setup_logger()

        try:

            self.validate_config()

            self.logger.info("Starting agent...")

            self.start_time = time.time()

            self.execute()
        except Exception as ex:
            self.logger.exception(f"[{self.name}] Errore durante l'esecuzione: {ex}")
        finally:
            elapsed = time.time() - self.start_time
            self.logger.info(
                f"execution completed in {elapsed:.3f} seconds."
            )

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent specific execution logic.
        """
        pass

    def stop(self):
        pass


class ThreadAgent(BaseAgent, threading.Thread):
    """
    Agent class based on threading.Thread.

    This class is a base class for all agents that need to run in a separate thread. It provides a common interface for
    the agent's lifecycle management.
    """

    def __init__(self, name: str | None = None,config=None, *args, **kwargs):
        threading.Thread.__init__(self, name=name)
        BaseAgent.__init__(self, name=name, config=config,*args, **kwargs)

        self._stop_event = threading.Event()

    def run(self):
        """
        Override of the `run` method of threading.Thread: it calls the common logic `run_agent`.
        """
        self.run_agent()

    def stop(self):
        """
        Event set to request the external stop of the thread.
        """
        self._stop_event.set()

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent execution logic.
        """
        pass


class ProcessAgent(BaseAgent, multiprocessing.Process):
    """
    Agent class based on multiprocessing.Process.

    This class is a base class for all agents that need to run in a separate process. It provides a common interface for
    the agent's lifecycle management.
    """

    def __init__(self, name: str | None = None,config=None, *args, **kwargs):
        multiprocessing.Process.__init__(self, name=name)
        BaseAgent.__init__(self, name=name,config=config, *args, **kwargs)

        self._stop_event = multiprocessing.Event()

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
