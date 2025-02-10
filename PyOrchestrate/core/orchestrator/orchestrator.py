import time
from collections import defaultdict, deque

from PyOrchestrate.core.agent.base_agent import BaseAgent
from .memory import OMemory, AgentEntry
from PyOrchestrate.core.utilities.event_manager import EventManager
from PyOrchestrate.core.utilities.event import OrchestratorEvent

from ..base.base import BaseClass


class OrchestratorConfig(BaseClass.Config):
    """
    Orchestrator configuration class.

    Attributes:
        check_interval (float): The interval to check the agents.
        logger (LoggerConfig): Logger configuration.
    """

    check_interval: float = 1

    def __init__(self, check_interval: float | None = None, **kwargs):
        super().__init__(**kwargs)

        if check_interval is not None:
            self.check_interval: float = check_interval

    def validate(self):
        super().validate()
        if self.check_interval <= 0:
            raise ValueError("Check interval must be greater than 0.")


class Orchestrator(BaseClass):
    """
    Orchestrator class to manages the agents.

    Attributes:
        memory (OMemory): Memory to store the agents.
        event_manager (EventManager): Manages events among agents.
        dependencies (dict[str, list[str]]): Dependencies among agents.
    """

    Config = OrchestratorConfig

    def __init__(self, name: str | None = None):
        super().__init__(name=name, config=Orchestrator.Config())

        self.setup_logger()
        self._info()
        self.config.validate()

        self.memory = OMemory()
        self.event_manager = EventManager()

        self.dependencies: dict[str, list[str]] = defaultdict(list)

    def register_agent(
        self,
        agent_class,
        name: str,
        custom_config: BaseClass.Config | None = None,
        control_events: BaseAgent.ControlEvents | None = None,
        state_events: BaseAgent.StateEvents | None = None,
        event_manager: EventManager | None = None,
        **kwargs,
    ) -> AgentEntry:
        """
        Register an agent on the orchestrator.

        Notes:
            After registering the agent, you can call the `start` method to start all agents.

        Warnings:
            agent_name must be unique.

        Args:
            agent_class: Class of the agent to register.
            name: Name of the agent.
            custom_config: Custom configuration for the agent.
            control_events: Control events for the agent.
            state_events: State events for the agent.
            event_manager: Event manager for the agent.
            kwargs: Additional arguments for the agent.

        Returns:
            AgentEntry: The agent entry object stored in the memory.
        """

        agent_entry = self.memory.add_agent(
            agent_class=agent_class,
            name=name,
            custom_config=custom_config,
            control_events=control_events,
            state_events=state_events,
            event_manager=event_manager,
            **kwargs,
        )
        self.logger.debug(f"Agent '{name}' registered.")
        return agent_entry

    def add_dependency(self, agent_name: str, depends_on: list[str]):
        """
        Aggiunge dipendenze: agent_name dipende da depends_on.
        """
        if agent_name not in [agent.name for agent in self.memory.agents]:
            raise ValueError(f"Agent {agent_name} non è registrato nell'Orchestrator.")
        for dependency in depends_on:
            if dependency not in [agent.name for agent in self.memory.agents]:
                raise ValueError(
                    f"Dipendenza {dependency} non è registrata nell'Orchestrator."
                )
        self.dependencies[agent_name].extend(depends_on)
        self.logger.info(f"Agent '{agent_name}' dipende da {depends_on}.")

    def validate_dependencies(self):
        """
        Check dependencies error (es. A -> B -> A).
        """
        visited = set()
        stack = set()

        agents = list(self.dependencies.keys())

        def visit(node):
            """Visit a node in the graph."""
            if node in stack:
                raise ValueError(
                    f"Rilevato un ciclo di dipendenze: {node} è parte di un ciclo."
                )
            if node not in visited:
                stack.add(node)
                for neighbor in self.dependencies[node]:
                    visit(neighbor)
                stack.remove(node)
                visited.add(node)

        for agent in agents:
            visit(agent)

    def _topological_sort_agents(self) -> list[str]:
        """
        Order agents topologically.

        Notes:
            This method uses a BFS algorithm to order the agents topologically.

        Returns:
            list[str]: Ordered agents.

        Raises:
            ValueError: If there is a cyclic dependency
        """
        all_agents: set[str] = {agent.name for agent in self.memory.agents}

        for ag in all_agents:
            if ag not in self.dependencies:
                self.dependencies[ag] = []

        in_degree: dict[str, int] = {ag: 0 for ag in all_agents}
        for ag, deps in self.dependencies.items():
            for dep in deps:
                in_degree[ag] += 1

        # BFS
        queue = deque(ag for ag in all_agents if in_degree[ag] == 0)
        topo_order = []

        while queue:
            node = queue.popleft()
            topo_order.append(node)
            for child, deps in self.dependencies.items():
                if node in deps:
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        queue.append(child)

        if len(topo_order) != len(all_agents):
            raise ValueError(
                "Non è possibile ottenere un ordinamento topologico: dipendenze cicliche?"
            )

        return topo_order

    def start(self):
        """
        Start all registered agents in the topological order of their dependencies.

        Notes:
            Before starting the agents, it validates the dependencies among agents.
            After starting the agents, it emits an `OrchestratorEvent.AGENT_STARTED` event for each agent. Only at this
            point will be created the agent instances.
        """

        self.start_time = time.time()

        self.validate_dependencies()

        ordered_agents = self._topological_sort_agents()

        for ag in ordered_agents:
            self._start_agent_callback(ag)

    def _start_agent_callback(self, agent_name: str):
        """
        Callback to start the agent.

        Notes:
            This method is used to start the agent and emit an `OrchestratorEvent.AGENT_STARTED` event for the agent.
        """
        agent: AgentEntry = self.memory.get_agent(agent_name)

        self.logger.info(f"Starting agent {agent_name}...")
        agent.initialize_agent()
        agent.start()
        self.event_manager.emit(OrchestratorEvent.AGENT_STARTED, agent_name=agent.name)

    def stop(self):
        """Terminates all registered agents."""
        for agent in self.memory.agents:
            agent.stop()
            self.logger.info(f"Stopping agent '{agent.name}'.")

    def join(self) -> None:
        """
        Check the status of all agents and wait for them to complete.

        Notes:
            This method blocks the current thread until all agents are completed.

            - When agent is completed, it emits an `OrchestratorEvent.AGENT_TERMINATED` event.
            - When all agents are completed, it emits an `OrchestratorEvent.ALL_AGENTS_COMPLETED` event.
        """

        all_finished: bool = False
        notified: set = set()

        while not all_finished:
            alive_count = 0

            for agent in self.memory.agents:

                if not agent.instance.is_alive():
                    if not agent.name in notified:
                        self.logger.info(f"Agent '{agent.name}' ended.")
                        self.event_manager.emit(
                            OrchestratorEvent.AGENT_TERMINATED,
                            agent_name=agent.name,
                        )
                        notified.add(agent.name)
                else:
                    alive_count += 1

            if alive_count == 0:
                all_finished = True
            else:
                time.sleep(self.config.check_interval)

        self.logger.info("All agents have completed.")
        self.event_manager.emit(OrchestratorEvent.ALL_AGENTS_COMPLETED)

        self.logger.debug(f"elapsed: {time.time() - self.start_time}")

    def simple_join(self) -> None:
        """
        Simple join method to wait for all processes or threads to complete their execution.
        """
        for agent in self.memory.agents:
            agent.join()
        self.logger.info("All processes or threads have completed.")
        self.event_manager.emit(OrchestratorEvent.ALL_AGENTS_COMPLETED)

        self.logger.debug(f"elapsed: {time.time() - self.start_time}")

    def report(self):
        """Report the status of all agents."""
        self.logger.info(f"Reporting {len(self.memory.agents)} agents status.")
        for agent in self.memory.agents:
            self.logger.info(agent.status())

    def _info(self):
        self.logger.debug(f"Config: check_interval={self.config.check_interval}")
