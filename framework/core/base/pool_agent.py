from abc import abstractmethod
from typing import final
from dataclasses import dataclass

from ..base.periodic_agent import PeriodicProcessAgent
from ...utilities.periodic_timer import PeriodicTimer
from ..orchestrator.orchestrator import Orchestrator
from ..orchestrator.memory import AgentEntry


class PoolAgent(PeriodicProcessAgent):
    """
    Pool agent class.

    This agent is an orchestrator of BaseThreadAgent instances.
    """

    @dataclass
    class Config(PeriodicProcessAgent.Config):
        """
        Pool agent configuration class.

        Attributes:
            agents_entry (list[AgentEntry]): List of agents to be registered.
            execution_interval (float): The interval between two consecutive executions.
            delay_compensation (bool): Compensate the delay in the execution.
            logger (LoggerConfig): Logger configuration.
        """

        execution_interval: float = 1
        delay_compensation: bool = False
        agents_entry: list[AgentEntry] = None

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

        self.timer = None
        self.interval = self.config.execution_interval
        self.compensate_delay = self.config.delay_compensation

        self._orchestrator = None

    def setup(self):
        self.timer = PeriodicTimer(
            logger=self.logger,
            interval=self.interval,
            compensate_delay=self.compensate_delay,
        )

        self._orchestrator = Orchestrator()

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
        for agent in self.orchestrator.memory.agents:
            if not agent.instance.is_alive():
                self.logger.info(f"Found dead agent {agent}. Stopping.")
                self.stop()
            else:
                self.logger.debug(f"Agent {agent} is running.")

    @property
    def orchestrator(self) -> Orchestrator:
        if self._orchestrator is None:
            raise RuntimeError("Orchestrator is not initialized")
        return self._orchestrator
