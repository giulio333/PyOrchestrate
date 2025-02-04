import datetime
import multiprocessing
import threading
from typing import Dict, List, Optional, Type, Any

from ..utilities.event_manager import EventManager
from ..agent import BaseAgent, AgentProtocol
from ..base import BaseClass


class AgentEntry:
    """
    AgentEntry is a class that stores metadata and the instance of an agent.

    Notes:
        You can access state and control events to manage the agent's lifecycle.

    Examples:
        >>> from PyOrchestrate.core.orchestrator import Orchestrator
        >>> from models import FileWriter # type: ignore
        >>>
        >>> orchestrator = Orchestrator("CoolOrchestrator")
        >>> fw_agent: AgentEntry = orchestrator.register_agent(FileWriter, "FileWriter")
        >>> orchestrator.start()
        >>> fw_agent.state_events.ready_event.wait()
        >>> print("agent is now ready")


    Attributes:
        agent_class (Type[BaseAgent]): The class of the agent.
        name (str): The name of the agent.
        control_events (BaseAgent.ControlEvents): Control events for the agent.
        state_events (BaseAgent.StateEvents): State events for the agent.
        config (Optional[BaseConfig]): Custom configuration for the agent.
        _record_event_callback (Optional[Any]): Callback to record events.
        kwargs (Any): Additional keyword arguments for the agent.
        instance (BaseAgent): The agent instance.

    Methods:
        start: Start the agent instance.
        stop: Stop the agent instance.
        join: Join the agent instance.
        restart: Restart the agent instance.
        status: Get the status of the agent
    """

    def __init__(
        self,
        agent_class,
        name: str,
        control_events: Optional[BaseAgent.ControlEvents] = None,
        state_events: Optional[BaseAgent.StateEvents] = None,
        config: Optional[BaseClass.Config] = None,
        record_event_callback: Optional[Any] = None,
        event_manager: Optional[EventManager] = None,
        **kwargs: Any,
    ):
        self.agent_class = agent_class
        self.name = name
        self.config = config
        self.kwargs = kwargs
        self._instance = None
        self._record_event_callback = record_event_callback

        self.control_events = control_events
        self.state_events = state_events
        self.event_manager = event_manager

    @property
    def instance(self) -> AgentProtocol:
        """
        Get the agent instance.

        Returns:
            BaseAgent: The agent instance.
        """
        assert self._instance is not None, "Agent instance not initialized yet."
        return self._instance

    def start(self) -> None:
        """
        Start the agent instance.
        """
        self.instance.start()
        self._record_event("start")

    def stop(self) -> None:
        """
        Stop the agent instance.
        """
        self.instance.stop()
        self._record_event("stop")

    def join(self) -> None:
        """
        Join the agent instance.
        """
        self.instance.join()
        self._record_event("join")

    def restart(self) -> None:
        """
        Restart the agent instance.
        """
        self.stop()
        self.join()
        # self.instance = self._create_instance()
        self.start()

    def is_alive(self) -> bool:
        """
        Check if the agent instance is alive.

        Returns:
            bool: True if the agent instance is alive, False otherwise.
        """
        return self.instance.is_alive()

    def status(self) -> str:
        """
        Get agent status.

        Notes:
            The status is a string containing the following information:

            - Whether the agent is alive.
            - Whether the agent is a daemon.
            - The agent's ident (if it is a process).
            - The agent's PID (if it is a process).

        Returns:
            str: Agent status.
        """

        if not self.instance:
            raise ValueError("Agent instance not initialized yet.")

        if self.instance.a_type == "process":
            alive: bool = self.instance.is_alive()
            daemon: bool = self.instance.daemon
            ident: int | None = self.instance.ident
            pid: int | None = self.instance.pid
        elif self.instance.a_type == "thread":
            alive = self.instance.is_alive()
            daemon = self.instance.daemon
            ident = None
            pid = None
        else:
            raise ValueError("Unknown agent type.")

        return f"{self.instance.name} -> alive: {alive} daemon: {daemon} ident: {ident} pid: {pid}"

    def initialize_agent(self) -> None:
        """
        Create agent instance.

        Notes:
            If custom agent configuration is not provided, the default configuration will be used (agent_class.Config).

        Returns:
            None
        """
        if self.config is None:
            self.config = self.agent_class.Config()

        params: dict[str, Any] = dict()
        params["name"] = self.name
        params["config"] = self.config
        params["control_events"] = self.control_events
        params["state_events"] = self.state_events
        params["event_manager"] = self.event_manager
        params.update(self.kwargs)

        self._instance = self.agent_class(**params)

    def _record_event(self, event_type: str) -> None:
        """
        Record an event for the agent.
        """
        if self._record_event_callback is not None:
            self._record_event_callback(self.name, event_type)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<AgentEntry: {self.name}>"


class Group:
    """
    A group of agents.
    """

    def __init__(self, name: str):
        self.name = name
        self.agent_names: List[str] = []

    def add_agent(self, agent_name: str) -> None:
        """
        Aggiunge un agente (rappresentato dal suo nome) al gruppo.
        """
        if agent_name not in self.agent_names:
            self.agent_names.append(agent_name)

    def remove_agent(self, agent_name: str) -> None:
        """
        Rimuove un agente dal gruppo.
        """
        if agent_name in self.agent_names:
            self.agent_names.remove(agent_name)


class OMemory:
    """
    OMemory is a class that stores agents and groups of agents.

    Agents are stored as `AgentEntry` objects, which contain some metadata and the agent instance.

    Attributes:
        _agents (Dict[str, AgentEntry]): Map from agent name to `AgentEntry` object.
        _groups (Dict[str, Group]): Map from group name to `Group` object.
        _agent_stats (Dict[str, List[Dict[str, Any]]]): mappa dell’agente con una lista di eventi registrati.

    Methods:
        add_agent: Add an agent to the orchestrator memory.
        get_agent_entry: Get the `AgentEntry` object corresponding to the provided name.
        get_agent_instance: Get the agent instance for the provided name.
        create_group: Create an empty group if it doesn't already exist.
        add_agent_to_group: Add an existing agent to the specified group.
        remove_agent_from_group: Remove an agent from the specified group.
        get_group: Get the `Group` object if it exists.
        get_group_agents: Get the list of agent instances belonging to the group.
        start_agent: Start the agent with the given name.
        stop_agent: Stop the agent with the given name.
        join_agent: Join the agent with the given name.
        restart_agent: Restart the agent with the given name.
        agents: Get the list of all `AgentEntry` objects
        get_agent_stats: Get the event log for the specified agent
    """

    def __init__(self) -> None:
        # Mappa dal nome dell’agente all’oggetto `AgentEntry`
        self._agents: Dict[str, AgentEntry] = {}
        # Mappa dal nome del gruppo all’oggetto `Group`
        self._groups: Dict[str, Group] = {}
        # Mappa dal nome dell’agente a una lista di eventi con timestamp
        self._agent_stats: Dict[str, List[Dict[str, Any]]] = {}

    @property
    def agents(self) -> list[AgentEntry]:
        """
        Return the list of all `AgentEntry` objects.

        These objects contain all the information needed to manage an agent.

        Returns:
            list[AgentEntry]: List of all agents.
        """
        return list(self._agents.values())

    def add_agent(
        self,
        agent_class: Type[BaseAgent],
        name: str,
        custom_config: Optional[BaseClass.Config] = None,
        control_events: Optional[BaseAgent.ControlEvents] = None,
        state_events: Optional[BaseAgent.StateEvents] = None,
        event_manager: Optional[EventManager] = None,
        **kwargs: Any,
    ) -> AgentEntry:
        """
        Store an agent in the orchestrator memory.

        Data will be stored as an `AgentEntry` object, which contains metadata and the agent instance. The agent will be
        initialized and its control events will be set to ready by default.

        Notes:
            Every agent has a set of events that can be used to control its lifecycle. By default, all `ControlEvents` are
            set to ready. If no custom events are provided, the default events will be created.

        Args:
            agent_class (Type[BaseAgent]): The class of the agent to store.
            name (str): The name of the agent.
            custom_config (BaseConfig, optional): Custom configuration for the agent. Defaults to None.
            control_events (BaseAgent.ControlEvents, optional): Control events for the agent. Defaults to None.
            state_events (BaseAgent.StateEvents, optional): State events for the agent. Defaults to None.
            event_manager (EventManager, optional): Event manager for the agent. Defaults to None.
            kwargs (Any): Additional keyword arguments for the agent.

        Returns:
            AgentEntry: The `AgentEntry` object corresponding to the stored agent.
        """

        if agent_class.a_type == "process":
            event = multiprocessing.Event
        elif agent_class.a_type == "thread":
            event = threading.Event  # type: ignore
        else:
            raise ValueError("Unknown agent type.")

        if not control_events:
            control_events = agent_class.ControlEvents(
                setup_event=event(), execute_event=event(), stop_event=event()
            )

            # default set to ready
            control_events.setup_event.set()
            control_events.execute_event.set()

        if not state_events:
            state_events = agent_class.StateEvents(
                ready_event=event(), close_event=event()
            )

        if not event_manager:
            event_manager = EventManager()

        entry = AgentEntry(
            agent_class=agent_class,
            name=name,
            control_events=control_events,
            state_events=state_events,
            config=custom_config,
            record_event_callback=self._record_event,
            event_manager=event_manager,
            **kwargs,
        )
        self._agents[name] = entry
        self._agent_stats[name] = []

        return entry

    def create_group(self, group_name: str) -> None:
        """
        Crea un gruppo vuoto, se non esiste già.
        """
        if group_name not in self._groups:
            self._groups[group_name] = Group(group_name)

    def add_agent_to_group(self, agent_name: str, group_name: str) -> None:
        """
        Aggiunge un agente esistente al gruppo specificato (se il gruppo esiste).
        """
        if agent_name in self._agents and group_name in self._groups:
            group = self._groups[group_name]
            group.add_agent(agent_name)

    def remove_agent_from_group(self, agent_name: str, group_name: str) -> None:
        """
        Rimuove un agente dal gruppo specificato (se il gruppo esiste).
        """
        if group_name in self._groups:
            group = self._groups[group_name]
            group.remove_agent(agent_name)

    def get_group(self, group_name: str) -> Optional[Group]:
        """
        Ritorna l'oggetto `Group`, se esiste.
        """
        return self._groups.get(group_name)

    def get_group_agents(self, group_name: str) -> List:
        """
        Ritorna la lista delle istanze degli agenti appartenenti al gruppo.
        """
        group = self._groups.get(group_name)
        if not group:
            return []
        instances = []
        for agent_name in group.agent_names:
            entry = self._agents.get(agent_name)
            if entry is not None:
                instances.append(entry.instance)
        return instances

    def get_agent_stats(self, agent_name: str) -> list[dict] | None:
        """
        Return the event log for the specified agent.

        If the agent does not exist or has no events, return None.

        Args:
            agent_name (str): The name of the agent.

        Returns:
            Optional[List[Dict[str, datetime]]]: The event log for the agent or None.
        """
        return self._agent_stats.get(agent_name)

    def get_agent(self, name: str) -> AgentEntry:
        """
        Get the `AgentEntry` object corresponding to the provided name.

        Args:
            name (str): The name of the agent to retrieve.

        Returns:
            AgentEntry | None: The `AgentEntry` object corresponding to the provided name, or None if not found.

        Raises:
            ValueError: If the agent is not found.
        """
        _ = self._agents.get(name)

        if not _:
            raise ValueError(f"Agent '{name}' not found.")

        return _

    def get_agent_instance(self, name: str):
        """
        Get the agent instance for the provided name.

        Args:
            name (str): The name of the agent to retrieve.

        Returns:
            ProcessAgent | ThreadAgent | None: The agent instance, or None if not found.
        """
        entry = self.get_agent(name)
        return entry.instance if entry else None

    def _record_event(self, agent_name: str, event_type: str) -> None:
        """
        Record an event for the specified agent.

        event = { "timestamp": datetime.datetime.now(), "event": "start" }

        Args:
            agent_name (str): The name of the agent.
            event_type (str): The type of event to record.

        Returns:
            None
        """
        now = datetime.datetime.now()
        event = {"timestamp": now, "event": event_type}
        if agent_name not in self._agent_stats:
            self._agent_stats[agent_name] = []
        self._agent_stats[agent_name].append(event)

    def __str__(self):
        return f"<OrchestratorMemory: {len(self._agents)} agents, {len(self._groups)} groups.>"
