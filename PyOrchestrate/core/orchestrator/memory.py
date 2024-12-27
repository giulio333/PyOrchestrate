import datetime
from typing import Dict, List, Optional, Type, Any

from ..base import BaseAgent, BaseConfig, ProcessAgent, ThreadAgent


class AgentEntry:
    """
    AgentEntry is a class that stores metadata and the instance of an agent.

    Attributes:
        agent_class (Type[BaseAgent]): The class of the agent.
        name (str): The name of the agent.
        config (Optional[BaseConfig]): Custom configuration for the agent.
        args (Any): Additional arguments for the agent.
        kwargs (Any): Additional keyword arguments for the agent.
        instance (BaseAgent): The agent instance.
        _record_event_callback (Optional[Any]): Callback to record events.

    Methods:
        start: Start the agent instance.
        stop: Stop the agent instance.
        join: Join the agent instance.
        restart: Restart the agent instance.
        status: Get the status of the agent
    """

    def __init__(
            self,
            agent_class: Type[BaseAgent],
            name: str,
            config: Optional[BaseConfig] = None,
            record_event_callback: Optional[Any] = None,
            *args: Any,
            **kwargs: Any
    ):
        self.agent_class = agent_class
        self.name = name
        self.config = config
        self.args = args
        self.kwargs = kwargs

        # callback per registrare eventi (arriva da OrchestratorMemory)
        self._record_event_callback = record_event_callback

        self.instance: BaseAgent = self._create_instance()

    def _create_instance(self) -> BaseAgent:
        """
        Create agent instance.
        """
        return self.agent_class(name=self.name, config=self.config, *self.args, **self.kwargs)

    def _record_event(self, event_type: str) -> None:
        """
        Invochiamo la callback se è presente.
        """
        if self._record_event_callback is not None:
            self._record_event_callback(self.name, event_type)

    def start(self) -> None:
        """
        Metodi “di comodo” per gestire l’agente
        """
        if hasattr(self.instance, 'start'):
            self.instance.start()
        self._record_event("start")

    def stop(self) -> None:
        """
        Arresta l’istanza, se supportato
        """
        if hasattr(self.instance, 'stop'):
            self.instance.stop()
        self._record_event("stop")

    def join(self) -> None:
        """
        Fa la join dell’istanza, se supportato
        """
        if hasattr(self.instance, 'join'):
            self.instance.join()
        self._record_event("join")

    def restart(self) -> None:
        """
        Restart the agent instance.
        """
        self.stop()
        self.join()
        self.instance = self._create_instance()
        self.start()

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

        alive: bool
        daemon: bool
        ident: int | None
        pid: int | None

        if isinstance(self.instance, ProcessAgent):
            alive: bool = self.instance.is_alive()
            daemon: bool = self.instance.daemon
            ident: int | None = self.instance.ident
            pid: int | None = self.instance.pid
        elif isinstance(self.instance, ThreadAgent):
            alive = self.instance.is_alive()
            daemon = self.instance.daemon
            ident = None
            pid = None
        else:
            raise ValueError("Unknown agent type.")

        return f"{self.instance.name} -> alive: {alive} daemon: {daemon} ident: {ident} pid: {pid}"

    def __str__(self):
        return self.name


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

    def __init__(self):
        # Mappa dal nome dell’agente all’oggetto `AgentEntry`
        self._agents: Dict[str, AgentEntry] = {}
        # Mappa dal nome del gruppo all’oggetto `Group`
        self._groups: Dict[str, Group] = {}
        # Mappa dal nome dell’agente a una lista di eventi con timestamp
        self._agent_stats: Dict[str, List[Dict[str, Any]]] = {}

    @property
    def agents(self) -> List[AgentEntry]:
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
            custom_config: Optional[BaseConfig] = None,
            *args: Any,
            **kwargs: Any
    ) -> None:
        """
        Store an agent in the orchestrator memory.

        Data will be stored as an `AgentEntry` object, which contains metadata and the agent instance.

        Args:
            agent_class (Type[BaseAgent]): The class of the agent to store.
            name (str): The name of the agent.
            custom_config (Optional[BaseConfig], optional): Custom configuration for the agent. Defaults to None.
        """

        entry = AgentEntry(
            agent_class=agent_class,
            name=name,
            config=custom_config,
            record_event_callback=self._record_event,
            *args,
            **kwargs
        )
        self._agents[name] = entry
        self._agent_stats[name] = []

    def get_agent_entry(self, name: str) -> Optional[AgentEntry]:
        """
        Ritorna l'oggetto `AgentEntry` corrispondente al nome fornito (se esiste).
        """
        return self._agents.get(name)

    def get_agent_instance(self, name: str) -> Optional[BaseAgent]:
        """
        Ritorna l’istanza dell’agente (se esiste).
        """
        entry = self.get_agent_entry(name)
        return entry.instance if entry else None

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

    def get_group_agents(self, group_name: str) -> List[BaseAgent]:
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

    def get_agent_stats(self, agent_name: str) -> Optional[List[Dict[str, datetime]]]:
        """
        Return the event log for the specified agent.

        If the agent does not exist or has no events, return None.

        Args:
            agent_name (str): The name of the agent.

        Returns:
            Optional[List[Dict[str, datetime]]]: The event log for the agent or None.
        """
        return self._agent_stats.get(agent_name)

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
        event = {
            "timestamp": now,
            "event": event_type
        }
        if agent_name not in self._agent_stats:
            self._agent_stats[agent_name] = []
        self._agent_stats[agent_name].append(event)

    def __str__(self):
        return f"<OrchestratorMemory: {len(self._agents)} agents, {len(self._groups)} groups.>"
