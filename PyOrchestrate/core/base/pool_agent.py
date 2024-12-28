from typing import final, TypeVar

from ..base.periodic_agent import PeriodicAgent
from ...utilities.periodic_timer import PeriodicTimer
from ..orchestrator.orchestrator import Orchestrator
from ..orchestrator.memory import AgentEntry


class PoolAgentConfig(PeriodicAgent.Config):
    def __init__(self, agents_entry: list[AgentEntry] | None = None, auto_reboot: bool = False, **kwargs):
        super().__init__(**kwargs)

        self.auto_reboot: bool = auto_reboot
        self.agents_entry: list[AgentEntry] = agents_entry if agents_entry else []

    def validate(self):
        super().validate()
        if self.limit is not None:
            raise ValueError("PoolAgent does not support limit parameter.")
        if not self.agents_entry:
            raise ValueError("No agents to register.")


T = TypeVar('T', bound=PoolAgentConfig)


class PoolAgent(PeriodicAgent[T]):
    """
    Pool agent class.

    This agent is an orchestrator of BaseThreadAgent instances.
    """

    class Config(PoolAgentConfig):
        """
        Pool agent configuration class.

        Attributes:
            auto_reboot (bool): Flag to enable automatic reboot of agents.
            agents_entry (list[AgentEntry]): List of agents to be registered.
            execution_interval (float): The interval of checking the agents.
            logger (LoggerConfig): Logger configuration.
        """
        pass

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

        self.timer = None
        self.interval = self.config.execution_interval
        self.compensate_delay = self.config.delay_compensation

        self._orchestrator = None

    def _info(self):
        super()._info()
        self.logger.debug(f"interval: {self.interval}")
        self.logger.debug(f"compensate_delay: {self.compensate_delay}")
        self.logger.debug(f"auto_reboot: {self.config.auto_reboot}")
        self.logger.debug(f"agents_entry: {self.config.agents_entry}")

    def setup(self):
        """
        Set up the PoolAgent.

        Notes:
            The PoolAgent act as an orchestrator for the agents. All agents found in the configuration are registered
            and started.

        Warnings:
            You can override this method to add custom setup logic but remember to call super().setup() to ensure the
            agent is correctly initialized.
        """
        super().setup()

        self._orchestrator = Orchestrator(name=self.name)

        if not self.config.agents_entry:
            self.logger.warning("No agents for current pool agent.")
            return

        for agent in self.config.agents_entry:
            self.orchestrator.register_agent(agent.agent_class, agent.name, agent.config)
        self.orchestrator.start()

    @final
    def runner(self):
        """
        Check the status of the agents and restart them if necessary.
        """
        if all(not agent.instance.is_alive() for agent in self.orchestrator.memory.agents):
            self.logger.info("All agents are stopped.")
            self.stop()
            return

    @property
    def orchestrator(self) -> Orchestrator:
        if self._orchestrator is None:
            raise RuntimeError("Orchestrator is not initialized")
        return self._orchestrator

    def _info(self):
        super()._info()
        self.logger.debug(f"auto_reboot: {self.config.auto_reboot}")
        self.logger.debug(f"agents_entry: {self.config.agents_entry}")
