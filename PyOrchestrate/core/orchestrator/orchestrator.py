from typing import Type
import time
from collections import defaultdict, deque

from .memory import OMemory
from PyOrchestrate.core.utilities.event_manager import EventManager
from PyOrchestrate.core.utilities.event import OrchestratorEvent

from ..base.base_agent import ProcessAgent, ThreadAgent
from ..base.base import BaseClass


class Orchestrator(BaseClass["Orchestrator.Config"]):
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

    class Config(BaseClass.Config):
        """
        Orchestrator configuration class.

        Attributes:
            check_interval (float): Interval to check the agents.
            logger (LoggerConfig): Logger configuration.

        Notes:
            Class attributes store default values for the configuration parameters. If you want to change the default
            values, you can override them in the derived class or pass them as arguments to the constructor.

            User-defined attributes follow the same pattern. They can be passed as arguments to the constructor or
            overridden in the derived class.

        Examples:
            You can create a custom configuration class by inheriting from the OrchestratorConfig class and overriding the
            desired attributes.

            >>> class Config(Orchestrator.Config):
            ...     check_interval = 2
            >>> default_config = Config()
            >>> custom_config = Config(check_interval=5)
        """
        check_interval: float = 1

        def __init__(self, check: bool = False, check_interval: float = 1, **kwargs):
            super().__init__(**kwargs)
            self.check_interval: float = check_interval

        def validate(self):
            super().validate()
            if self.check_interval <= 0:
                raise ValueError("Check interval must be greater than 0.")

    def __init__(self, name: str):
        super().__init__(name=name, config=Orchestrator.Config())

        self.setup_logger()
        self._info()
        self.config.validate()
        self.memory = OMemory()
        self.event_manager = EventManager()
        self.dependencies: dict[str, list] = defaultdict(list)

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

    def add_dependency(self, agent_name: str, depends_on: list[str]):
        if agent_name not in [agent.name for agent in self.memory.agents]:
            raise ValueError(f"Agent {agent_name} is not registered in the Orchestrator.")
        for dependency in depends_on:
            if dependency not in [agent.name for agent in self.memory.agents]:
                raise ValueError(f"Dependency {dependency} is not registered in the Orchestrator.")
        self.dependencies[agent_name].extend(depends_on)
        self.logger.info(f"Agent {agent_name} depends on {depends_on}.")

    def validate_dependencies(self):
        """
        Verifica che le dipendenze non abbiano cicli.
        """
        visited = set()
        stack = set()

        agents = list(self.dependencies.keys())

        def visit(node):
            if node in stack:
                raise ValueError(f"Dependency cycle detected: {node} is part of a cycle.")
            if node not in visited:
                stack.add(node)
                for neighbor in self.dependencies[node]:
                    visit(neighbor)
                stack.remove(node)
                visited.add(node)

        for agent in agents:
            visit(agent)

    def start(self):
        """
        Start all the agents registered in the orchestrator.

        Notes:
            This method will start all the agents registered in the orchestrator. It will check the dependencies between
            the agents and start them in the correct order.

        Raises:
            ValueError: If an agent is registered as a dependency but is not registered in the orchestrator.
            RuntimeError: If an agent cannot be started due to unsatisfied dependencies.
        """
        self.validate_dependencies()

        all_agents = {agent.name for agent in self.memory.agents}

        # in_degree: number of dependencies for each agent
        in_degree = {agent_name: 0 for agent_name in all_agents}
        for agent_name, deps in self.dependencies.items():
            for dep_name in deps:
                if dep_name not in all_agents:
                    raise ValueError(f"Agent {dep_name} is not registered in the Orchestrator.")
                in_degree[agent_name] += 1

        queue = deque(agent for agent in in_degree if in_degree[agent] == 0)
        started_agents = []

        while queue:
            current = queue.popleft()
            agent = self.memory.get_agent(current)
            self.logger.info(f"Starting agent {agent.name}...")

            agent.start()

            self.event_manager.emit(OrchestratorEvent.AGENT_STARTED.value, agent_name=agent.name)
            started_agents.append(current)

            # decrease in-degree of dependent agents
            for dependent_agent_name, deps in self.dependencies.items():
                if current in deps:
                    in_degree[dependent_agent_name] -= 1
                    # append to queue if in-degree is 0
                    if in_degree[dependent_agent_name] == 0:
                        queue.append(dependent_agent_name)

        # check if all agents have been started
        if len(started_agents) != len(all_agents):
            missing = all_agents - set(started_agents)
            raise RuntimeError("Some agents could not be started due to unsatisfied dependencies: " + str(missing))

        self.logger.info("All agents started.")

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

    def _info(self):
        self.logger.debug(f"Config: check_interval: {self.config.check_interval}")
