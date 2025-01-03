import time
import threading
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

        def __init__(self, check_interval: float = 1, **kwargs):
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

        # Mappa agent -> lista di stringhe (nomi agent da cui dipende)
        self.dependencies: dict[str, list[str]] = defaultdict(list)
        # Mappa agent -> ritardo di avvio (in secondi)
        self.agent_schedules: dict[str, float] = defaultdict(float)

        # Terrà i Timer avviati
        self._timers: list[threading.Timer] = []
        # Per tracciare quando (timestamp) un agent è stato effettivamente schedulato
        self._start_times: dict[str, float] = {}
        # Per semplificare: segna se un agente è partito
        self._started_agents: set[str] = set()

    def register_agent(
            self,
            agent_class: type[ProcessAgent | ThreadAgent],
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
        self.logger.info(f"Agent '{name}' registrato con start_delay={start_delay}.")

        if start_time:
            now = datetime.now().timestamp()
            # se definisci start_time, calcoliamo quanto manca da "ora"
            start_delay = start_time.timestamp() - now

        self.agent_schedules[name] = start_delay

    def add_dependency(self, agent_name: str, depends_on: list[str]):
        """
        Aggiunge dipendenze: agent_name dipende da depends_on.
        """
        if agent_name not in [agent.name for agent in self.memory.agents]:
            raise ValueError(f"Agent {agent_name} non è registrato nell'Orchestrator.")
        for dependency in depends_on:
            if dependency not in [agent.name for agent in self.memory.agents]:
                raise ValueError(f"Dipendenza {dependency} non è registrata nell'Orchestrator.")
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
                raise ValueError(f"Rilevato un ciclo di dipendenze: {node} è parte di un ciclo.")
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
            raise ValueError("Non è possibile ottenere un ordinamento topologico: dipendenze cicliche?")

        return topo_order

    def start(self):
        """
        Start all registered agents.
        """
        self.validate_dependencies()

        ordered_agents = self._topological_sort_agents()

        now = time.time()
        for ag in ordered_agents:
            deps = self.dependencies[ag]
            if deps:
                earliest_dep_start = max(self._start_times.get(dep, now) for dep in deps)
            else:
                earliest_dep_start = now

            desired_start = earliest_dep_start + self.agent_schedules[ag]
            self._start_times[ag] = desired_start

        for ag in ordered_agents:
            agent_obj = self.memory.get_agent(ag)
            desired_start = self._start_times[ag]
            delay = desired_start - time.time()
            if delay < 0:
                delay = 0

            self.logger.info(f"Schedulo l'avvio di '{ag}' tra {delay:.2f} secondi.")
            t = threading.Timer(delay, self._start_agent_callback, args=[ag])
            t.start()
            self._timers.append(t)

    def _start_agent_callback(self, agent_name: str):
        """
        Callback to start the agent.
        """
        if agent_name in self._started_agents:
            return

        agent = self.memory.get_agent(agent_name)

        self.logger.info(f"Starting agent {agent_name}... (delay={self.agent_schedules[agent_name]}s)")
        agent.start()
        self.event_manager.emit(OrchestratorEvent.AGENT_STARTED.value, agent_name=agent.name)

        self._started_agents.add(agent_name)

    def stop(self):
        """Terminates all registered agents."""
        for agent in self.memory.agents:
            agent.stop()
            self.logger.info(f"Stopping agent '{agent.name}'.")

        # Se ci sono Timer ancora non scattati, li cancelliamo
        for t in self._timers:
            if t.is_alive():
                t.cancel()
        self._timers.clear()

    def join(self) -> None:
        """
        Waits for all agents to complete.

        Notes:
            This method blocks the current thread until all agents are completed.

            - When agent is completed, it emits an `OrchestratorEvent.AGENT_TERMINATED` event.
            - When all agents are completed, it emits an `OrchestratorEvent.ALL_AGENTS_COMPLETED` event.
        """

        all_finished = False
        notified = set()

        while not all_finished:
            alive_count = 0

            for agent in self.memory.agents:
                if not hasattr(agent, "instance") or agent.instance is None:
                    alive_count += 1
                    continue

                if not agent.instance.is_alive():
                    if not agent.name in notified:
                        self.logger.info(f"Agent '{agent.name}' ended.")
                        self.event_manager.emit(OrchestratorEvent.AGENT_TERMINATED.value, agent_name=agent.name)
                        notified.add(agent.name)
                else:
                    alive_count += 1

            if alive_count == 0:
                all_finished = True
            else:
                time.sleep(self.config.check_interval)

        self.logger.info("All agents have completed.")
        self.event_manager.emit(OrchestratorEvent.ALL_AGENTS_COMPLETED.value)

    def report(self):
        """Report the status of all agents."""
        self.logger.info(f"Reporting {len(self.memory.agents)} agents status.")
        for agent in self.memory.agents:
            self.logger.info(agent.status())

    def _info(self):
        self.logger.debug(f"Config: check_interval={self.config.check_interval}")
