from typing import Type

from ..base.baseagent import AbstractBaseAgent, BaseConfig
from ...utilities.logguru import LoggerFactory


class Orchestrator:

    def __init__(self):
        self.agents: dict[str, AbstractBaseAgent] = {}
        self.logger = LoggerFactory().create_logger(
            "Orchestrator", "Orchestrator", "INFO"
        )

    def add_agent(
            self,
            agent_class: Type[AbstractBaseAgent],
            name: str,
            custom_config: BaseConfig | None = None,
            *args,
            **kwargs,
    ):

        agent_instance = agent_class(name, custom_config, *args, **kwargs)

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
