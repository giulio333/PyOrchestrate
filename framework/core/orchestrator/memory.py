from typing import Dict, List, Optional, Type

from ..base.baseagent import AbstractBaseAgent, BaseConfig

from typing import Type, Optional, Any
from ..base.baseagent import AbstractBaseAgent, BaseConfig


class AgentEntry:
    """
    AgentEntry is a class that stores metadata and the instance of an agent.
    """

    def __init__(
            self,
            agent_class: Type[AbstractBaseAgent],
            name: str,
            config: Optional[BaseConfig] = None,
            *args: Any,
            **kwargs: Any
    ):
        self.agent_class = agent_class
        self.name = name
        self.config = config
        self.args = args
        self.kwargs = kwargs

        self.instance: AbstractBaseAgent = self._create_instance()

    def _create_instance(self) -> AbstractBaseAgent:
        """
        Create agent instance.
        """
        return self.agent_class(self.name, self.config, *self.args, **self.kwargs)

    def start(self) -> None:
        """
        Metodi “di comodo” per gestire l’agente
        """
        if hasattr(self.instance, 'start'):
            self.instance.start()

    def stop(self) -> None:
        """
        Arresta l’istanza, se supportato
        """
        if hasattr(self.instance, 'stop'):
            self.instance.stop()

    def join(self) -> None:
        """
        Fa la join dell’istanza, se supportato
        """
        if hasattr(self.instance, 'join'):
            self.instance.join()

    def restart(self) -> None:
        """
        Restart the agent instance.
        """
        self.stop()
        self.join()
        self.instance = self._create_instance()
        self.start()

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


class OrchestratorMemory:
    """
    OrchestratorMemory is a class that stores agents and groups of agents.

    Agents are stored as `AgentEntry` objects, which contain some metadata and the agent instance.

    Attributes:
        _agents (Dict[str, AgentEntry]): Map from agent name to `AgentEntry` object.
        _groups (Dict[str, Group]): Map from group name to `Group` object.

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
    """

    def __init__(self):
        # Mappa dal nome dell’agente all’oggetto `AgentEntry`
        self._agents: Dict[str, AgentEntry] = {}
        # Mappa dal nome del gruppo all’oggetto `Group`
        self._groups: Dict[str, Group] = {}

    def add_agent(
            self,
            agent_class: Type[AbstractBaseAgent],
            name: str,
            custom_config: Optional[BaseConfig] = None,
            *args: Any,
            **kwargs: Any
    ) -> None:
        """
        Crea e memorizza un agente, costruendo un oggetto `AgentEntry`.
        """

        entry = AgentEntry(agent_class, name, custom_config, *args, **kwargs)
        self._agents[name] = entry

    def get_agent_entry(self, name: str) -> Optional[AgentEntry]:
        """
        Ritorna l'oggetto `AgentEntry` corrispondente al nome fornito (se esiste).
        """

        return self._agents.get(name)

    def get_agent_instance(self, name: str) -> Optional[AbstractBaseAgent]:
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

    def get_group_agents(self, group_name: str) -> List[AbstractBaseAgent]:
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

    def start_agent(self, name: str) -> None:
        """
        Start the agent with the given name.
        """

        entry = self.get_agent_entry(name)
        if entry:
            entry.start()

    def stop_agent(self, name: str) -> None:
        """
        Stop the agent with the given name.
        """

        entry = self.get_agent_entry(name)
        if entry:
            entry.stop()

    def join_agent(self, name: str) -> None:
        """
        Join the agent with the given name.
        """

        entry = self.get_agent_entry(name)
        if entry:
            entry.join()

    def restart_agent(self, name: str) -> None:
        """
        Restart the agent with the given name.
        """

        entry = self.get_agent_entry(name)
        if entry:
            entry.restart()

    @property
    def agents(self) -> list[AgentEntry]:
        """
        Return the list of all `AgentEntry` objects.

        These objects contain all the information needed to manage an agent.

        Returns:
            list[AgentEntry]: List of all agents.
        """

        return [agent for agent in self._agents.values()]
