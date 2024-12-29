from typing import Type
import time

from .memory import OMemory
from PyOrchestrate.core.utilities.event_manager import EventManager
from PyOrchestrate.core.utilities.event import OrchestratorEvent

from ..base.base_agent import ProcessAgent, ThreadAgent
from ..base.base import BaseClass


class OConfig(BaseClass.Config):
    """
    Orchestrator configuration class.

    Attributes:
        check_interval (float): Interval to check the agents.
        check (bool): Flag to enable the agent check.
        logger (LoggerConfig): Logger configuration.
    """

    def __init__(self, check: bool = False, check_interval: float = 1, **kwargs):
        super().__init__(**kwargs)
        self.check_interval: float = check_interval
        self.check: bool = check
        self.orchestrator_type = "base"

    def validate(self):
        if self.check_interval <= 0:
            raise ValueError("Check interval must be greater than 0.")


class Orchestrator(BaseClass[OConfig]):
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

    class Config(OConfig):
        pass

    def __init__(self, name: str, config: OConfig | None = None):
        if config is None:
            config = Orchestrator.Config()
        super().__init__(name=name, config=config)

        self.setup_logger()
        self.config.validate()
        self.memory = OMemory()
        self.event_manager = EventManager()

    def register_agent(
            self,
            agent_class: Type[ProcessAgent | ThreadAgent],
            name: str,
            custom_config: BaseClass.Config | None = None,
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

        self.memory.add_agent(agent_class=agent_class, name=name, custom_config=custom_config, **kwargs)
        self.logger.info(f"Agent {name} registered.")

    def start(self):
        """Start all the agents registered in the orchestrator."""
        for agent in self.memory.agents:
            agent.start()
            self.logger.info(f"Starting agent {agent}.")
            self.event_manager.emit(OrchestratorEvent.AGENT_STARTED.value, agent_name=agent.name)

    def stop(self):
        """Terminates all registered agents."""
        for agent in self.memory.agents:
            agent.stop()
            self.logger.info(f"Stopping agent {agent}.")

    def join(self):
        """
        Monitor and join all agents.

        Notes:
            This method will wait for all agents to complete. It will check the status of the stored agents at regular
            intervals (config.check_interval).

            When an agent completes, will emit the OrchestratorEvent.AGENT_TERMINATED vent.
            When all agents are completed, will emit the OrchestratorEvent.ALL_AGENTS_COMPLETED event.
        """
        active_agents = set(self.memory.agents)

        while active_agents:
            completed_agents = []
            for agent in active_agents:
                if not agent.instance.is_alive():
                    self.logger.info(f"Agent {agent} ended.")
                    self.event_manager.emit(OrchestratorEvent.AGENT_TERMINATED.value, agent_name=agent.name)
                    completed_agents.append(agent)

            # refresh active agents list
            for agent in completed_agents:
                active_agents.remove(agent)

            time.sleep(self.config.check_interval)

        self.logger.info("All agents completed.")
        self.event_manager.emit(OrchestratorEvent.ALL_AGENTS_COMPLETED.value)

    def report(self):
        """Report the status of all agents."""
        self.logger.info(f"Reporting {len(self.memory.agents)} agents status.")
        for agent in self.memory.agents:
            self.logger.info(agent.status())
