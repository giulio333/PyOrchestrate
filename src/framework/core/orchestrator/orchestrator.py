from typing import Type

from framework.core.base.baseagent import AbstractBaseAgent
from framework.utilities.logguru import LoggerFactory


class Orchestrator:

    def __init__(self):
        """Inizializza un Orchestrator vuoto."""
        self.agents: dict[str, AbstractBaseAgent] = {}
        self.logger = LoggerFactory().create_logger(
            "Orchestrator", "Orchestrator", level="INFO"
        )

    def add_agent(
        self,
        agent_class: Type[AbstractBaseAgent],
        name: str,
        custom_config: dict = {},
        *args,
        **kwargs,
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
