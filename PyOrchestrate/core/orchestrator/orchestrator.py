from typing import Type
import time
from collections import defaultdict, deque
from datetime import datetime

from .memory import OMemory
from PyOrchestrate.core.utilities.event_manager import EventManager
from PyOrchestrate.core.utilities.event import OrchestratorEvent

from ..base.base_agent import ProcessAgent, ThreadAgent
from ..base.base import BaseClass


class Orchestrator(BaseClass["Orchestrator.Config"]):
    """
    Orchestrator class to manages the agents.

    Attributes:
        memory (OMemory): Memory to store the agents.
        event_manager (EventManager): Manages events among agents.
        dependencies (dict[str, list[str]]): Dependencies among agents.
        agent_schedules (dict[str, float]): Mappa ogni agente a un ritardo (in secondi).
    """

    class Config(BaseClass.Config):
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
        self.dependencies: dict[str, list[str]] = defaultdict(list)

        self.agent_schedules: dict[str, float] = defaultdict(float)

    def register_agent(
            self,
            agent_class: Type[ProcessAgent | ThreadAgent],
            name: str,
            custom_config: BaseClass.Config | None = None,
            start_delay: float = 0.0,
            start_time: datetime | None = None,
            **kwargs,
    ):
        """
        Register an agent on the orchestrator.

        Args:
            agent_class: Class of the agent to register.
            name: Name of the agent.
            custom_config: Custom configuration for the agent.
            start_delay: Ritardo (in secondi) prima di avviare l'agente.
            start_time: Orario di avvio dell'agente.
        """

        self.memory.add_agent(agent_class=agent_class, name=name, custom_config=custom_config, **kwargs)
        self.logger.info(f"Agent {name} registered.")

        if start_time:
            now = datetime.now().timestamp()
            start_delay = start_time.timestamp() - now

        self.agent_schedules[name] = start_delay

    def add_dependency(self, agent_name: str, depends_on: list[str]):
        if agent_name not in [agent.name for agent in self.memory.agents]:
            raise ValueError(f"Agent {agent_name} is not registered in the Orchestrator.")
        for dependency in depends_on:
            if dependency not in [agent.name for agent in self.memory.agents]:
                raise ValueError(f"Dependency {dependency} is not registered in the Orchestrator.")
        self.dependencies[agent_name].extend(depends_on)
        self.logger.info(f"Agent {agent_name} depends on {depends_on}.")

    def validate_dependencies(self):
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
        self.validate_dependencies()

        # BUG: some times the agents are not started in the correct scheduled order

        all_agents = {agent.name for agent in self.memory.agents}
        in_degree = {agent_name: 0 for agent_name in all_agents}
        for agent_name, deps in self.dependencies.items():
            for dep_name in deps:
                if dep_name not in all_agents:
                    raise ValueError(f"Agent {dep_name} is not registered in the Orchestrator.")
                in_degree[agent_name] += 1

        queue = deque(agent for agent in in_degree if in_degree[agent] == 0)
        start_times = {agent: 0.0 for agent in all_agents}
        started_agents = []

        while queue:
            current = queue.popleft()
            agent = self.memory.get_agent(current)

            deps = self.dependencies[current]
            if deps:
                earliest_dep_start = max(start_times[dep] for dep in deps)
            else:
                earliest_dep_start = time.time()  # no dependencies, start immediately
            desired_start = max(earliest_dep_start, time.time()) + self.agent_schedules[current]

            while True:
                now = time.time()
                self._check_completed_agents()

                if now >= desired_start:
                    break  # exit and start the agent
                else:
                    time.sleep(self.config.check_interval)

            self.logger.info(f"Starting agent {agent.name}...")
            agent.start()
            self.event_manager.emit(OrchestratorEvent.AGENT_STARTED.value, agent_name=agent.name)

            start_times[current] = time.time()
            started_agents.append(current)

            # update in-degree and queue
            for dependent_agent_name, deps in self.dependencies.items():
                if current in deps:
                    in_degree[dependent_agent_name] -= 1
                    if in_degree[dependent_agent_name] == 0:
                        queue.append(dependent_agent_name)

        if len(started_agents) != len(all_agents):
            missing = all_agents - set(started_agents)
            raise RuntimeError(
                "Some agents could not be started due to unsatisfied dependencies: " + str(missing)
            )

    def _check_completed_agents(self):
        """
        Piccolo metodo di utilità per controllare chi è morto e notificare subito.
        """
        for agent in self.memory.agents:

            if not hasattr(agent, "instance"):
                continue

            if not agent.instance.is_alive():
                self.logger.info(f"Agent {agent.name} ended.")
                self.event_manager.emit(OrchestratorEvent.AGENT_TERMINATED.value, agent_name=agent.name)

    def stop(self):
        """Terminates all registered agents."""
        for agent in self.memory.agents:
            agent.stop()
            self.logger.info(f"Stopping agent {agent}.")

    def join(self):
        active_agents = set(self.memory.agents)

        while active_agents:
            completed_agents = []
            for agent in active_agents:
                if not agent.instance.is_alive():
                    self.logger.info(f"Agent {agent.name} ended.")
                    self.event_manager.emit(OrchestratorEvent.AGENT_TERMINATED.value, agent_name=agent.name)
                    completed_agents.append(agent)

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
