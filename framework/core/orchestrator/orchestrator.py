from typing import Type
import uuid

from .memory import OMemory
from ..base.baseagent import AbstractBaseAgent, BaseConfig
from ...utilities.logguru import LoggerFactory


class Orchestrator:

    def __init__(self):
        self.logger = LoggerFactory().create_logger(
            "Orchestrator", "Orchestrator", "INFO"
        )
        self.memory = OMemory()

    def register_agent(
            self,
            agent_class: Type[AbstractBaseAgent],
            name: str,
            custom_config: BaseConfig | None = None,
            *args,
            **kwargs,
    ):
        """
        Register an agent on current orchestrator.

        Args:
            agent_class: Class of the agent to register.
            name: Name of the agent.
            custom_config: Custom configuration for the agent.

        Returns:
            None
        """
        self.memory.add_agent(agent_class, name, custom_config, *args, **kwargs)
        self.logger.info(f"Agent {name} registered.")

    def start(self):
        """Start all the agents registered in the orchestrator."""
        for agent in self.memory.agents:
            agent.start()
            self.logger.info(f"Starting agent {agent}.")

    def stop(self):
        """Terminates all registered agents."""
        for agent in self.memory.agents:
            agent.stop()
            self.logger.info(f"Stopping agent {agent}.")

    def join(self):
        """Wait for all the agents to complete."""
        for agent in self.memory.agents:
            agent.join()
            self.logger.info(f"Agent {agent} ended.")
