import threading
import multiprocessing
import time
from abc import ABC, abstractmethod
from loguru import logger

from .base import BaseClass

class BaseAgent(BaseClass, ABC):
    """
    Abstract base class for all agents.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = None

    @logger.catch(reraise=True)
    def validate_config(self):
        """
        Validate the configuration.
        """

        self.config.validate()
        self.logger.info("Configuration successfully validated.")

    def run_agent(self):

        self.setup_logger()
        self.validate_config()

        self.logger.info("Starting agent...")

        self.start_time = time.time()

        try:
            self.execute()
        except Exception as ex:
            self.logger.exception(f"[{self.name}] Errore durante l'esecuzione: {ex}")
        finally:
            if self.stop_callback:
                self.stop_callback(self.name)
            elapsed = time.time() - self.start_time
            self.logger.info(
                f"execution completed in {elapsed:.3f} seconds."
            )

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent execution logic.
        """
        pass

    def stop(self):
        pass


class BaseThreadAgent(BaseAgent, threading.Thread):

    def __init__(self, name: str | None = None, *args, **kwargs):
        threading.Thread.__init__(self, name=name)
        BaseAgent.__init__(self, name, *args, **kwargs)

        self._stop_event = threading.Event()

    def run(self):
        """
        Override del metodo `run` di threading.Thread: richiama la logica comune `run_agent`.
        """
        self.run_agent()

    def stop(self):
        """
        Facoltativo: set di un event per richiedere lo stop esterno del thread.
        """
        self._stop_event.set()

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent execution logic.
        """
        pass


class BaseProcessAgent(BaseAgent, multiprocessing.Process):

    def __init__(self, name: str | None = None, *args, **kwargs):
        multiprocessing.Process.__init__(self, name=name)
        BaseAgent.__init__(self, name, *args, **kwargs)

        self._stop_event = multiprocessing.Event()

    def run(self):
        """
        Override del metodo `run` di multiprocessing.Process: richiama la logica comune `run_agent`.
        """
        self.run_agent()

    def stop(self):
        """
        Facoltativo: set di un event per richiedere lo stop esterno del processo.
        """
        self._stop_event.set()

    @abstractmethod
    def execute(self):
        """
        Abstract method to be implemented in derived classes: Agent execution logic.
        """
        pass
