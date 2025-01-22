from abc import ABC
from typing import final, TypeVar
import threading
import multiprocessing

from ..base.periodic_agent import PeriodicAgent
from ..orchestrator.orchestrator import Orchestrator
from ..orchestrator.memory import AgentEntry


class PoolAgentConfig(PeriodicAgent.Config):
    """
    Pool agent configuration class.

    Attributes:
        auto_reboot (bool): Flag to enable automatic reboot of agents.
        agents_entry (list[AgentEntry]): List of agents to be registered.
        execution_interval (float): The interval of checking the agents.
        delay_compensation (bool): Compensate the delay in the execution.
        logger (LoggerConfig): Logger configuration.

    Notes:
        Class attributes store default values for the configuration parameters. If you want to change the default
        values, you can override them in the derived class or pass them as arguments to the constructor.

        User-defined attributes follow the same pattern. They can be passed as arguments to the constructor or
        overridden in the derived class.

    Examples:
        You can create a custom configuration class by inheriting from the PoolAgentConfig class and overriding the
        desired attributes.

        >>> class Config(PoolAgent.Config):
        ...     agent_entry = [AgentEntry(...), AgentEntry(...)]
        ...     auto_reboot = True
        >>> default_config = Config()
        >>> custom_config = Config(auto_reboot=False)
    """

    agent_entry: list[AgentEntry] | None = None
    auto_reboot: bool = False

    def __init__(
        self,
        agents_entry: list[AgentEntry] | None = None,
        auto_reboot: bool | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if auto_reboot is not None:
            self.auto_reboot: bool = auto_reboot

        if agents_entry is not None:
            self.agents_entry: list[AgentEntry] = agents_entry

    def validate(self):
        super().validate()
        if self.limit is not None:
            raise ValueError("PoolAgent does not support limit parameter.")
        if not self.agents_entry:
            raise ValueError("No agents to register.")


T = TypeVar("T", bound=PoolAgentConfig)


class PoolAgent(PeriodicAgent[T]):
    """
    Pool agent class.

    This agent is an orchestrator of BaseThreadAgent instances.
    """

    Config = PoolAgentConfig

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

        self.timer = None
        self.interval = self.config.execution_interval
        self.compensate_delay = self.config.delay_compensation

        self._orchestrator = None

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
            self.orchestrator.register_agent(
                agent.agent_class,
                agent.name,
                agent.config,
                agent.control_events,
                agent.state_events,
                **agent.kwargs,
            )
        self.orchestrator.start()

    @final
    def runner(self):
        """
        Check the status of the agents and restart them if necessary.
        """
        self.pre_runner()
        if all(
            not agent.instance.is_alive() for agent in self.orchestrator.memory.agents
        ):
            self.logger.info("All agents are stopped.")
            self.stop()
            return
        self.post_runner()

    def pre_runner(self):
        """
        @temaplate

        Run before the runner method.
        """
        pass

    def post_runner(self):
        """
        @template

        Run after the runner method.
        """
        pass

    @property
    def orchestrator(self) -> Orchestrator:
        if self._orchestrator is None:
            raise RuntimeError("Orchestrator is not initialized")
        return self._orchestrator

    def _info(self):
        super()._info()
        self.logger.debug(f"Config: auto_reboot: {self.config.auto_reboot}")
        self.logger.debug(f"Config: agents_entry: {self.config.agents_entry}")


class PoolProcessAgent(PoolAgent[T], multiprocessing.Process, ABC):
    a_type: str = "process"

    def __init__(self, name: str, config: T, **kwargs):
        multiprocessing.Process.__init__(self, name=name)
        PoolAgent.__init__(self, name=name, config=config, a_type="process", **kwargs)


class PoolThreadAgent(PoolAgent[T], threading.Thread, ABC):
    a_type: str = "thread"

    def __init__(self, name: str, config: T, **kwargs):
        threading.Thread.__init__(self, name=name)
        PoolAgent.__init__(self, name=name, config=config, a_type="thread", **kwargs)
