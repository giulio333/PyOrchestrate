import multiprocessing
import threading
from abc import ABC, abstractmethod
import logging

from framework.utilities.logguru import LoggerFactory


class BaseAgent(ABC):
    def __init__(self, name=None, log_level=logging.INFO):
        """Inizializza un agente di base."""
        self.name = name if name else self.__class__.__name__

        # Configurazione del logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(log_level)
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(handler)

    def setup_logger(self):
        """
        Configura il logger del processo. Le configurazioni vengono estratte da `LoggerConfig`.

        tip:
            E' possibile sovrascrivere questo metodo per personalizzare il logger.

        Returns:
            Logger: Istanza del logger configurato.
        """

        if hasattr(self, "logger"):
            return

        # estrazione configurazioni da BaseConfig.LoggerConfig
        # logger_config: LoggerConfig = self.config.logger
        level: str = "TRACE"  # logger_config.level
        filename: str = self.name  # logger_config.filename.capitalize() or self.name

        self.logger = LoggerFactory.create_logger(
            log_identifier=filename, logger_name=filename, level=level
        )

        self.logger.info(
            f"Logger configurato: log_file={self.name}.log, level={level}",
        )

    def run(self):
        """Metodo eseguito dall'agente (processo o thread)."""
        self.logger.info(f"Inizio dell'esecuzione: {self.name}", logging.INFO)
        try:
            self.execute()
        except Exception as e:
            self.logger.exception(f"Errore durante l'esecuzione: {e}", logging.ERROR)
        finally:
            self.logger.critical(f"Fine dell'esecuzione: {self.name}", logging.INFO)

    @abstractmethod
    def execute(self):
        """Metodo astratto da implementare per definire la logica dell'agente."""
        pass


class ProcessAgent(BaseAgent, multiprocessing.Process):
    def __init__(self, *args, **kwargs):
        BaseAgent.__init__(self, *args, **kwargs)
        multiprocessing.Process.__init__(self)

    def run(self):
        BaseAgent.run(self)


class ThreadAgent(BaseAgent, threading.Thread):
    def __init__(self, *args, **kwargs):
        BaseAgent.__init__(self, *args, **kwargs)
        threading.Thread.__init__(self)

    def run(self):
        BaseAgent.run(self)
