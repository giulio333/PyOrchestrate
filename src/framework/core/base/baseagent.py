import multiprocessing
import threading
from abc import ABC, abstractmethod
import logging
import time
import os, sys
from dataclasses import dataclass
from loguru import logger
from typing import Type

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from framework.utilities.logguru import LoggerFactory
from framework.core.base.exceptions import TerminateProcess


import threading
import multiprocessing
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass


class BaseConfig(ABC):
    """
    Classe base per la configurazione.
    """

    @classmethod
    def validate(cls):
        """Valida la configurazione (metodo facoltativo)."""
        pass


@dataclass
class LoggerConfig:
    level: str = "DEBUG"
    filename: str = ""


class AbstractBaseAgent(ABC):
    """
    Classe astratta che racchiude la logica comune a tutti gli agenti:
    - setup del logger
    - validazione della configurazione
    - metodo astratto execute
    """

    class Config(BaseConfig):
        """
        Configurazione dell'agente.

        Attributes:
            logger (LoggerConfig): Configurazione del logger.
        """

        logger: LoggerConfig = LoggerConfig()
        cycles: int = 5

    def __init__(self, name: str | None = None, *args, **kwargs):
        self.name: str = name or self.__class__.__name__
        self.start_time = 0.0

    @logger.catch(reraise=False)
    def setup_logger(self):
        """
        Configura il logger in base a `Config.logger`.
        """

        if hasattr(self, "logger"):
            return

        logger_cfg = self.Config.logger
        logging_level = getattr(logging, logger_cfg.level.upper(), "INFO")
        log_name = logger_cfg.filename or self.name

        # Configurazione di base del logger
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            level=logging_level,
        )

        self.logger = LoggerFactory.create_logger(
            log_identifier=log_name, logger_name=log_name, level=logging_level
        )
        self.logger.info(
            f"[{self.name}] Logger configurato a livello: {logger_cfg.level}"
        )

    @logger.catch(reraise=False)
    def validate_config(self):
        """
        Esegue la validazione della configurazione.
        """

        self.Config.validate()
        self.logger.debug(f"[{self.name}] Configurazione validata: {self.Config}")

    def run_agent(self):
        """
        Logica di avvio comune: prepara logger, valida config, gestisce eccezioni, etc.
        """

        self.setup_logger()
        self.validate_config()

        self.logger.info(f"[{self.name}] Avvio dell'esecuzione...")
        self.start_time = time.time()

        try:
            self.execute()
        except Exception as ex:
            self.logger.exception(f"[{self.name}] Errore durante l'esecuzione: {ex}")
        finally:
            elapsed = time.time() - self.start_time
            self.logger.info(
                f"[{self.name}] Esecuzione terminata in {elapsed:.2f} secondi"
            )

    @abstractmethod
    def execute(self):
        """
        Metodo astratto da implementare nelle classi derivate:
        la logica del “lavoro” effettivo.
        """
        pass

    @abstractmethod
    def stop(self):
        """
        Metodo astratto da implementare nelle classi derivate:
        richiesta di stop dell'agente.
        """
        pass


class BaseThreadAgent(AbstractBaseAgent, threading.Thread):
    """
    Agente base che utilizza un thread per l'esecuzione.
    """

    def __init__(self, name: str | None = None, *args, **kwargs):
        # Inizializzo il thread
        threading.Thread.__init__(self, name=name)

        # Inizializzo la parte AbstractBaseAgent
        AbstractBaseAgent.__init__(self, name)

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
        self.logger.info(f"[{self.name}] Richiesta di stop ricevuta.")


class BaseProcessAgent(AbstractBaseAgent, multiprocessing.Process):
    """
    Agente base che utilizza un processo per l'esecuzione.
    """

    def __init__(self, name: str | None = None, *args, **kwargs):

        # Inizializzo il process
        multiprocessing.Process.__init__(self, name=name)

        # Inizializzo la parte AbstractBaseAgent
        AbstractBaseAgent.__init__(self, name, *args, **kwargs)

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
        # if self.logger:
        #     self.logger.info(f"[{self.name}] Richiesta di stop ricevuta.")


class LoopingAgent(BaseProcessAgent):

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def execute(self):
        """Esegue un loop continuo finché non viene richiesto di fermarsi."""
        self.logger.info(f"{self.name} ha iniziato il loop.")
        while not self._stop_event.is_set():
            self.do_work()
            time.sleep(1)  # Pausa tra le iterazioni del loop

    @abstractmethod
    def do_work(self):
        """Definisce il lavoro da eseguire in ogni iterazione del loop."""
        pass


class Orchestrator:

    def __init__(self):
        """Inizializza un Orchestrator vuoto."""
        self.agents: dict[str, AbstractBaseAgent] = {}
        self.logger = LoggerFactory().create_logger(
            "Orchestrator", "Orchestrator", level="INFO"
        )

    def add_agent(
        self, agent_class: Type[AbstractBaseAgent], name: str, *args, **kwargs
    ):
        """Aggiunge un nuovo agente all'Orchestrator.

        Args:
            agent_class (type): La classe dell'agente da istanziare.
            agent_type (str): Il tipo di agente, 'process' o 'thread'. Default è 'process'.
            *args: Argomenti posizionali per il costruttore dell'agente.
            **kwargs: Argomenti keyword per il costruttore dell'agente.

        Raises:
            ValueError: Se il tipo di agente non è valido.
        """

        agent_instance = agent_class(name, *args, **kwargs)

        unique_name = f"{name}_{len(self.agents)}"

        self.agents.update({unique_name: agent_instance})

        self.logger.info(f"Agente {name} aggiunto.")

    def start(self):
        """Avvia tutti gli agenti registrati."""

        for agent in self.agents:
            agent_instance: AbstractBaseAgent = self.agents[agent]
            agent_instance.start()  # type: ignore
            self.logger.info(f"Agente {agent} avviato.")

    def join(self):
        """Attende il completamento di tutti gli agenti registrati."""
        for agent in self.agents:
            agent_instance: AbstractBaseAgent = self.agents[agent]
            agent_instance.join()  # type: ignore
            self.logger.info(f"Agente {agent} completato.")

    def stop(self):
        """Termina tutti gli agenti registrati.

        Note:
            Questa funzione tenta di terminare i processi o thread. Per i processi utilizza
            `terminate()`; per i thread, è necessaria una logica specifica nell'implementazione
            degli agenti.
        """
        for agent in self.agents:
            agent_instance: AbstractBaseAgent = self.agents[agent]
            agent_instance.stop()
            self.logger.info(f"Agente {agent} fermato.")


# Esempio di agente "concreto" che lavora in loop
class FileWriter(LoopingAgent):

    def __init__(self, name: str, message):
        super().__init__(
            name,
        )

        self.message = message

    class Config(LoopingAgent.Config):
        num_iterations: int = 5

    def do_work(self):

        self.Config.num_iterations -= 1

        if self.Config.num_iterations == 0:
            self.stop()

        with open(f"{self.name}_log.txt", "a") as log_file:
            log_message = f"[{self.name}] {self.message}\n"
            log_file.write(log_message)
        self.logger.debug(log_message.strip())
        time.sleep(1)  # Evita di saturare la CPU


if __name__ == "__main__":

    o = Orchestrator()
    o.add_agent(FileWriter, name="AgentThread1", message="Hello")
    o.add_agent(FileWriter, name="AgentThread2", message="World")

    o.start()
    o.join()
