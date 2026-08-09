import datetime
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Type, Any

from PyOrchestrate.core.agent import BaseAgent, AgentProtocol
from PyOrchestrate.core.base import BaseClass


class AgentLifecycleState(Enum):
    """Parent-process lifecycle state for an orchestrated agent entry."""

    REGISTERED = "registered"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    TERMINATED = "terminated"
    FAILED = "failed"
    QUARANTINED = "quarantined"


@dataclass(frozen=True, slots=True)
class AgentStartAttempt:
    """Identity of one prepared startup generation."""

    agent_name: str
    generation_id: int


class AgentEntry:
    """
    AgentEntry is a class that stores metadata and the instance of an agent.

    Notes:
        You can access state and control events to manage the agent's lifecycle.

    Examples:
        >>> from PyOrchestrate.core.orchestrator import Orchestrator
        >>> from models import FileWriter
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
        plugin (Optional[BasePlugin]): Custom plugin for the agent.
        _record_event_callback (Optional[Any]): Callback to record events.
        kwargs (Any): Additional keyword arguments for the agent.
        instance (BaseAgent): The agent instance.

    """

    def __init__(
        self,
        agent_class: Type[AgentProtocol],
        name: str,
        control_events: Optional[BaseAgent.ControlEvents] = None,
        state_events: Optional[BaseAgent.StateEvents] = None,
        config: Optional[BaseClass.Config] = None,
        plugin: Optional[BaseClass.Plugin] = None,
        record_event_callback: Optional[Any] = None,
        **kwargs: Any,
    ):
        self.agent_class = agent_class
        self.name = name
        self.config = config
        self.plugin = plugin
        self.kwargs = kwargs
        self._instance = None
        self._instance_generation_id: int | None = None
        self._record_event_callback = record_event_callback
        self._state = AgentLifecycleState.REGISTERED
        self._state_lock = threading.RLock()
        self._start_cancel_requested = threading.Event()
        self._generation_id = 0
        self._active_start_attempt: AgentStartAttempt | None = None
        self._stop_requested_generation_id: int | None = None

        self.control_events = control_events
        self.state_events = state_events

    @property
    def state(self) -> AgentLifecycleState:
        """Return the lifecycle state tracked by the orchestrator process."""
        with self._state_lock:
            return self._state

    def _transition_to(
        self,
        state: AgentLifecycleState,
        allowed_from: set[AgentLifecycleState],
    ) -> None:
        """Perform a validated parent-process lifecycle transition."""
        with self._state_lock:
            if self._state not in allowed_from:
                allowed = ", ".join(sorted(item.value for item in allowed_from))
                raise RuntimeError(
                    f"Agent '{self.name}' cannot transition from "
                    f"'{self._state.value}' to '{state.value}'; "
                    f"expected one of: {allowed}."
                )
            self._state = state

    def _prepare_start(self) -> AgentStartAttempt:
        """Allocate and enter one startup attempt atomically."""
        with self._state_lock:
            allowed = {
                AgentLifecycleState.REGISTERED,
                AgentLifecycleState.TERMINATED,
                AgentLifecycleState.FAILED,
            }
            if self._state not in allowed:
                expected = ", ".join(sorted(item.value for item in allowed))
                raise RuntimeError(
                    f"Agent '{self.name}' cannot transition from "
                    f"'{self._state.value}' to "
                    f"'{AgentLifecycleState.STARTING.value}'; "
                    f"expected one of: {expected}."
                )
            if self._instance is not None and self._instance.is_alive():
                raise RuntimeError(
                    f"Cannot prepare agent '{self.name}' while it is alive."
                )

            self._generation_id += 1
            attempt = AgentStartAttempt(self.name, self._generation_id)
            # A dead previous generation is no longer the instance owned by
            # this attempt. Constructor failures must therefore leave no
            # current instance to clean up.
            self._instance = None
            self._instance_generation_id = None
            self._active_start_attempt = attempt
            self._stop_requested_generation_id = None
            self._start_cancel_requested.clear()
            self._state = AgentLifecycleState.STARTING
            return attempt

    def _validate_attempt_unlocked(self, attempt: AgentStartAttempt) -> None:
        if attempt.agent_name != self.name or self._active_start_attempt != attempt:
            raise RuntimeError(
                f"Startup attempt {attempt.generation_id} is not active "
                f"for agent '{self.name}'."
            )

    def _transition_attempt_to(
        self,
        attempt: AgentStartAttempt,
        state: AgentLifecycleState,
        allowed_from: set[AgentLifecycleState],
    ) -> None:
        """Transition only when ``attempt`` still owns this entry."""
        with self._state_lock:
            self._validate_attempt_unlocked(attempt)
            if self._state not in allowed_from:
                allowed = ", ".join(sorted(item.value for item in allowed_from))
                raise RuntimeError(
                    f"Agent '{self.name}' attempt {attempt.generation_id} "
                    f"cannot transition from '{self._state.value}' to "
                    f"'{state.value}'; expected one of: {allowed}."
                )
            self._state = state

    def _request_stop(
        self,
    ) -> tuple[AgentLifecycleState, AgentStartAttempt | None]:
        """Atomically cancel the current attempt and enter a stop state."""
        with self._state_lock:
            previous = self._state
            attempt = self._active_start_attempt
            if previous is AgentLifecycleState.REGISTERED:
                self._state = AgentLifecycleState.TERMINATED
            elif previous is AgentLifecycleState.STARTING:
                self._start_cancel_requested.set()
                self._state = AgentLifecycleState.STOPPING
            elif previous in {
                AgentLifecycleState.RUNNING,
                AgentLifecycleState.QUARANTINED,
            }:
                self._state = AgentLifecycleState.STOPPING
            return previous, attempt

    def _attempt_cancel_requested(self, attempt: AgentStartAttempt) -> bool:
        with self._state_lock:
            self._validate_attempt_unlocked(attempt)
            return self._start_cancel_requested.is_set()

    @property
    def generation_id(self) -> int:
        """Return the generation assigned to the current instance."""
        with self._state_lock:
            return self._generation_id

    @property
    def is_initialized(self) -> bool:
        """Return whether the concrete thread/process instance exists."""
        with self._state_lock:
            return self._instance is not None

    def _has_instance(self, attempt: AgentStartAttempt) -> bool:
        """Return whether ``attempt`` owns the current concrete instance."""
        with self._state_lock:
            return (
                self._active_start_attempt == attempt
                and self._instance is not None
                and self._instance_generation_id == attempt.generation_id
            )

    @property
    def instance(self) -> AgentProtocol:
        """
        Get the agent instance.

        Notes:
            An entry only has an instance once a startup attempt created one, so
            a registered or queued agent has none. Use `is_initialized` to check
            before reading this.

            The guard used to be an `assert`, which `python -O` strips: the
            property then returned `None`, turning a clear failure here into an
            `AttributeError` somewhere further away.

        Returns:
            BaseAgent: The agent instance.

        Raises:
            RuntimeError: If the agent has no instance yet.
        """
        if self._instance is None:
            raise RuntimeError(
                f"Agent '{self.name}' has no instance yet: it is "
                f"'{self.state.value}' and has not been started."
            )
        return self._instance

    def _start_instance(self, attempt: AgentStartAttempt | None = None) -> bool:
        """Start only if ``attempt`` is still authoritative and uncancelled."""
        with self._state_lock:
            resolved = attempt or self._active_start_attempt
            if resolved is None:
                raise RuntimeError(
                    f"Agent '{self.name}' has no initialized startup attempt."
                )
            self._validate_attempt_unlocked(resolved)
            if attempt is not None:
                if (
                    self._state is not AgentLifecycleState.STARTING
                    or self._start_cancel_requested.is_set()
                ):
                    return False
            if (
                self._instance is None
                or self._instance_generation_id != resolved.generation_id
            ):
                raise RuntimeError(
                    f"Agent '{self.name}' attempt {resolved.generation_id} "
                    "has no matching instance."
                )
            self._instance.start()
            self._record_event("start")
            return True

    def _stop_instance(self, attempt: AgentStartAttempt | None = None) -> bool:
        """Claim and request stop at most once for one generation."""
        with self._state_lock:
            resolved = attempt or self._active_start_attempt
            if (
                resolved is None
                or self._instance is None
                or self._instance_generation_id != resolved.generation_id
                or self._active_start_attempt != resolved
                or self._stop_requested_generation_id == resolved.generation_id
            ):
                return False
            self._stop_requested_generation_id = resolved.generation_id
            instance = self._instance

        instance.stop()
        self._record_event("stop")
        return True

    def _join_instance(
        self,
        timeout: float | None = None,
        attempt: AgentStartAttempt | None = None,
    ) -> bool:
        """Join only the instance belonging to ``attempt``."""
        with self._state_lock:
            resolved = attempt or self._active_start_attempt
            if (
                resolved is None
                or self._instance is None
                or self._instance_generation_id != resolved.generation_id
                or self._active_start_attempt != resolved
            ):
                return False
            instance = self._instance

        instance.join(timeout=timeout)
        self._record_event("join")
        return True

    @property
    def start_cancel_requested(self) -> bool:
        """Return whether startup cancellation was requested."""
        return self._start_cancel_requested.is_set()

    def is_alive(self, attempt: AgentStartAttempt | None = None) -> bool:
        """
        Check if the agent instance is alive.

        Returns:
            bool: True if the agent instance is alive, False otherwise.
        """
        with self._state_lock:
            if self._instance is None:
                return False
            if attempt is not None and (
                self._active_start_attempt != attempt
                or self._instance_generation_id != attempt.generation_id
            ):
                return False
            instance = self._instance
        return instance.is_alive()

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

        if not self.is_initialized:
            return (
                f"{self.name} -> state: {self.state.value} alive: False "
                "daemon: False ident: None pid: None"
            )

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

    def _initialize_instance(self, attempt: AgentStartAttempt | None = None) -> bool:
        """
        Create agent instance.

        Notes:
            - If custom agent configuration is not provided, the default
                configuration will be used (agent_class.Config).
            - If custom agent plugin is not provided, the default plugin will
                be used (agent_class.Plugin).

        Returns:
            None
        """
        lifecycle_owned = attempt is not None
        with self._state_lock:
            if attempt is None:
                if self._instance is not None and self._instance.is_alive():
                    raise RuntimeError(
                        f"Cannot initialize agent '{self.name}' while it is alive."
                    )
                self._generation_id += 1
                attempt = AgentStartAttempt(self.name, self._generation_id)
                self._instance = None
                self._instance_generation_id = None
                self._active_start_attempt = attempt
                self._stop_requested_generation_id = None
            else:
                self._validate_attempt_unlocked(attempt)
                if (
                    self._state is not AgentLifecycleState.STARTING
                    or self._start_cancel_requested.is_set()
                ):
                    return False

            params: dict[str, Any] = dict()
            params["name"] = self.name
            params["config"] = self.config
            params["plugin"] = self.plugin
            params["control_events"] = self.control_events
            params["state_events"] = self.state_events
            params.update(self.kwargs)
            # Lifecycle identity is owned by the entry and cannot be
            # overridden through registration kwargs.
            params["generation_id"] = attempt.generation_id

        # Agent constructors may perform user-defined, blocking work. Keep that
        # work outside the entry lock so a concurrent stop can cancel startup.
        instance = self.agent_class(**params)

        with self._state_lock:
            self._validate_attempt_unlocked(attempt)
            self._instance = instance
            self._instance_generation_id = attempt.generation_id

            # Keep the entry and concrete instance on the same event objects.
            # This also makes startup timeout protection work when callers rely
            # on the agent's default event containers.
            self.control_events = getattr(
                instance, "control_events", self.control_events
            )
            self.state_events = getattr(instance, "state_events", self.state_events)
            if self.state_events:
                self.state_events.start_event.clear()
                self.state_events.ready_event.clear()
                self.state_events.close_event.clear()
            if self.control_events:
                self.control_events.stop_event.clear()
            return (
                self._state is AgentLifecycleState.STARTING
                and not self._start_cancel_requested.is_set()
                if lifecycle_owned
                else True
            )

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
        Adds an agent (identified by its name) to the group.
        """
        if agent_name not in self.agent_names:
            self.agent_names.append(agent_name)

    def remove_agent(self, agent_name: str) -> None:
        """
        Removes an agent from the group.
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
        _agents_history (Dict[str, List[Dict[str, Any]]]): Map from agent name to a list of recorded events.

    """

    def __init__(self) -> None:
        # Map from agent name to its `AgentEntry` object
        self._agents: Dict[str, AgentEntry] = {}
        # Map from group name to its `Group` object
        self._groups: Dict[str, Group] = {}
        # Map from agent name to a list of timestamped events
        self._agents_history: Dict[str, List[Dict[str, Any]]] = {}

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
        agent_class: Type[AgentProtocol],
        name: str,
        custom_config: Optional[BaseClass.Config] = None,
        custom_plugin: Optional[BaseClass.Plugin] = None,
        control_events: Optional[BaseAgent.ControlEvents] = None,
        state_events: Optional[BaseAgent.StateEvents] = None,
        **kwargs: Any,
    ) -> AgentEntry:
        """
        Store an agent in the orchestrator memory.

        Data will be stored as an `AgentEntry` object, which contains metadata and the agent instance. The agent will be
        initialized and its control events will be set to ready by default.

        Notes:
            Every agent has a set of events that can be used to control its lifecycle. By default, all `ControlEvents` are
            set to ready. If no custom events are provided, the default events will be created.

            Events from agents are handled centrally by the orchestrator's event manager.
            Agents communicate with the orchestrator via message channel.

        Args:
            agent_class (Type[BaseAgent]): The class of the agent to store.
            name (str): The name of the agent.
            custom_config (BaseConfig, optional): Custom configuration for the agent. Defaults to None.
            custom_plugin (BasePlugin, optional): Custom plugin for the agent. Defaults to None.
            control_events (BaseAgent.ControlEvents, optional): Control events for the agent. Defaults to None.
            state_events (BaseAgent.StateEvents, optional): State events for the agent. Defaults to None.
            kwargs (Any): Additional keyword arguments for the agent.

        Returns:
            AgentEntry: The `AgentEntry` object corresponding to the stored agent.

        Raises:
            ValueError: If the agent already exists.
        """

        if name in self._agents:
            raise ValueError(f"Agent '{name}' already exists.")

        entry = AgentEntry(
            agent_class=agent_class,
            name=name,
            control_events=control_events,
            state_events=state_events,
            config=custom_config,
            plugin=custom_plugin,
            record_event_callback=self._record_event,
            **kwargs,
        )
        self._agents[name] = entry
        self._agents_history[name] = []

        return entry

    def create_group(self, group_name: str) -> None:
        """
        Creates an empty group, unless it already exists.
        """
        if group_name not in self._groups:
            self._groups[group_name] = Group(group_name)

    def add_agent_to_group(self, agent_name: str, group_name: str) -> None:
        """
        Adds an existing agent to the given group, when the group exists.
        """
        if agent_name in self._agents and group_name in self._groups:
            group = self._groups[group_name]
            group.add_agent(agent_name)

    def remove_agent_from_group(self, agent_name: str, group_name: str) -> None:
        """
        Removes an agent from the given group, when the group exists.
        """
        if group_name in self._groups:
            group = self._groups[group_name]
            group.remove_agent(agent_name)

    def get_group(self, group_name: str) -> Optional[Group]:
        """
        Returns the `Group` object, when it exists.
        """
        return self._groups.get(group_name)

    def get_group_agents(self, group_name: str) -> List[AgentProtocol]:
        """
        Returns the list of agent instances belonging to the group.

        Notes:
            Only agents that have been started have an instance. A member that
            is merely registered, or still waiting in the worker queue, is
            skipped: reading `entry.instance` for it used to raise instead of
            returning the group's running agents.
        """
        group = self._groups.get(group_name)
        if not group:
            return []
        instances: List[AgentProtocol] = []
        for agent_name in group.agent_names:
            entry = self._agents.get(agent_name)
            if entry is not None and entry.is_initialized:
                instances.append(entry.instance)
        return instances

    def get_agent_stats(
        self, agent_name: str
    ) -> list[dict[str, datetime.datetime]] | None:
        """
        Return the event log for the specified agent.

        If the agent does not exist or has no events, return None.

        Args:
            agent_name (str): The name of the agent.

        Returns:
            Optional[List[Dict[str, datetime]]]: The event log for the agent or None.
        """
        return self._agents_history.get(agent_name)

    def get_agent(self, name: str) -> AgentEntry | None:
        """
        Get the `AgentEntry` object corresponding to the provided name.

        Args:
            name (str): The name of the agent to retrieve.

        Returns:
            AgentEntry | None: The `AgentEntry` object corresponding to the provided name, or None if not found.

        Raises:
            ValueError: If the agent is not found.
        """
        return self._agents.get(name)

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
        event: dict[str, datetime.datetime | str] = {
            "timestamp": now,
            "event": event_type,
        }
        if agent_name not in self._agents_history:
            self._agents_history[agent_name] = []
        self._agents_history[agent_name].append(event)

    def __str__(self):
        return f"<OrchestratorMemory: {len(self._agents)} agents, {len(self._groups)} groups.>"
