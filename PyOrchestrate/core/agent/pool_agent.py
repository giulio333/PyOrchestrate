from abc import ABC
from typing import final, List
import threading
import multiprocessing

from PyOrchestrate.core.agent.periodic_agent import PeriodicAgent
from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator
from PyOrchestrate.core.orchestrator.memory import AgentEntry
from PyOrchestrate.core.utilities.validation import ValidationResult, ValidationSeverity


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
        Creating a custom configuration for a PoolAgent:

        >>> class PoolAgentConfig(PeriodicAgent.Config):
        ...     auto_reboot = True  # Default auto reboot flag
        ...     agents_entry = [AgentEntry(...), AgentEntry(...)]  # Default agents entry list
        ...     execution_interval = 2  # Default execution interval
        ...     delay_compensation = True  # Default delay compensation

        >>> # Default configuration
        >>> default_pool_config = PoolAgentConfig()

        >>> # Custom configuration
        >>> custom_pool_config = PoolAgentConfig(
        ...     auto_reboot=False,
        ...     agents_entry=[AgentEntry(...), AgentEntry(...)],
        ...     execution_interval=1,
        ...     delay_compensation=False
        ... )
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

    def validate(self) -> List[ValidationResult]:
        """
        Implementation of specific validation for PoolAgent.

        Returns:
            List[ValidationResult]: List of validation results.
        """
        results = super().validate()

        # Check if there are agents to register
        if not hasattr(self, "agents_entry") or not self.agents_entry:
            results.append(
                ValidationResult(
                    field="agents_entry",
                    message="No agents to register.",
                    severity=ValidationSeverity.WARNING,
                )
            )

        return results


class PoolAgent(PeriodicAgent):
    """
    Pool agent class.

    This agent is an orchestrator of BaseThreadAgent instances.
    """

    Config = PoolAgentConfig

    def __init__(self, name: str | None = None, **kwargs):
        super().__init__(name=name, **kwargs)

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


class PoolProcessAgent(PoolAgent, multiprocessing.Process, ABC):
    """
    PoolProcessAgent class.

    This class provides a common interface for agents that execute a cycle method in a loop using a separate process.

    Args:
        PoolAgent (_type_): PoolAgent class.
        multiprocessing (_type_): multiprocessing module.
        ABC (_type_): Abstract base class.
    """

    def __init__(self, name: str | None = None, **kwargs):
        """
        Initialize a new PoolProcessAgent.

        Args:
            name (str | None, optional): The name of the agent. Defaults to None.
        """
        multiprocessing.Process.__init__(self, name=name)
        PoolAgent.__init__(self, name=name, a_type="process", **kwargs)


class PoolThreadAgent(PoolAgent, threading.Thread, ABC):
    """
    PoolThreadAgent class.
    This class provides a common interface for agents that execute a cycle method in a loop using a separate thread.

    Args:
        PoolAgent (_type_): PoolAgent class.
        threading (_type_): threading module.
        ABC (_type_): Abstract base class.
    """

    def __init__(self, name: str | None = None, **kwargs):
        """
        Initialize a new PoolThreadAgent.

        Args:
            name (str | None, optional): The name of the agent. Defaults to None.
        """
        threading.Thread.__init__(self, name=name)
        PoolAgent.__init__(self, name=name, a_type="thread", **kwargs)
