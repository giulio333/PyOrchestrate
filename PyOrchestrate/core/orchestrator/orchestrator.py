from typing import Type

from .memory import OMemory

from ..base import BaseAgent, BaseConfig, BaseClass, ThreadAgent


class Orchestrator(BaseClass):
    """
    Orchestrator class to manages the agents.

    Notes:
        You can pass custom configuration, same as the agent configuration.

    Examples:
        >>> from PyOrchestrate.core.base.utilities import LoggerConfig
        >>> Orchestrator.Config(logger=LoggerConfig("INFO", "Orchestrator"))

    Attributes:
        memory (OMemory): Memory to store the agents.

    Methods:
        register_agent: Register an agent on the orchestrator.
        start: Start all the agents registered in the orchestrator.
        stop: Terminates all registered agents.
        join: Wait for all the agents to complete.
    """

    def __init__(self, config: BaseConfig | None = None):
        super().__init__(name="Orchestrator", config=config)
        self.logger = None
        self.memory = OMemory()

        self.setup_logger()

    def register_agent(
            self,
            agent_class: Type[BaseAgent],
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

        self.memory.add_agent(agent_class=agent_class, name=name, custom_config=custom_config, *args, **kwargs)
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

    def report(self):
        """Report the status of all agents."""
        self.logger.info(f"Reporting {len(self.memory.agents)} agents status.")
        for agent in self.memory.agents:
            self.logger.info(agent.status())

    def on_agent_stopped(self, agent_name: str):
        """
        Callback to be called when an agent is stopped.

        Args:
            agent_name: The name of the agent that stopped.
        """
        self.logger.info(f"callback Agent {agent_name} stopped.")
