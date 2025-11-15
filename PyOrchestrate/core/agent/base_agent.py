"""
BaseAgent module.
"""

import threading
import multiprocessing
import time
from abc import ABC, abstractmethod
from typing import final, Protocol, Literal, Optional, List
from enum import Enum
from datetime import datetime

from PyOrchestrate.core.base.base import BaseClass
from PyOrchestrate.core.utilities.event import AgentEvent
from PyOrchestrate.core.plugins.plugin_manager import PluginManager
from PyOrchestrate.core.plugins.heartbeat import AgentHeartbeatTimerPlugin
from PyOrchestrate.core.utilities.validation import (
    ConfigValidationError,
    ConfigValidationWarning,
)
from PyOrchestrate.core.utilities.messaging import MessageChannel, ServiceMessage


class AgentTerminationStatus(Enum):
    """Represents the termination status of an agent."""

    SUCCESS = "success"  # Normal termination
    WARNING = "warning"  # Terminated with warnings
    ERROR = "error"  # Terminated with errors
    CRITICAL = "critical"  # Terminated with critical errors


class AgentConfig(BaseClass.Config):
    """
    Base agent configuration class.

    Class attributes store default values for configuration parameters. These values can be
    overridden either in derived classes or through constructor arguments.

    User-defined attributes follow the same pattern, they can be set via constructor
    arguments or overridden in derived classes.

    Attributes:
        logger_config (LoggerConfig): Configuration for the logger.
        validation_policy (ValidationPolicy): Policy for validation management.

    Examples:
        Creating a custom configuration for a ChatAgent:

        >>> class ChatAgentConfig(BaseAgent.Config):
        ...     model_name = "gpt-3.5-turbo"  # Default model name
        ...     max_tokens = 1000             # Default maximum tokens per request
        ...     temperature = 0.7             # Default temperature for sampling

        >>> # Default configuration
        >>> default_chat_config = ChatAgentConfig()

        >>> # Custom configuration
        >>> custom_chat_config = ChatAgentConfig(
        ...     model_name="gpt-4",
        ...     max_tokens=2000,
        ...     temperature=0.9
        ... )
    """

    pass


class AgentPlugin(BaseClass.Plugin):
    """
    Plugin class for agents.

    This class can contain various plugins that extend agent functionality.
    """

    heartbeat: AgentHeartbeatTimerPlugin | None = None

    def __init__(self, heartbeat: AgentHeartbeatTimerPlugin | None = None, **kwargs):
        super().__init__(**kwargs)

        if heartbeat is not None:
            self.heartbeat = heartbeat


class BaseAgent(BaseClass, ABC):
    """
    Abstract base class for all agents.

    This class provides a common interface for agent lifecycle management, defining
    the essential methods that an agent must implement.

    Each agent manages two types of events:

    - state_events: For managing the agent's internal state
    - control_events: For handling external commands

    Events are communicated to the orchestrator via message channel, allowing
    centralized event management and coordination. The orchestrator handles
    all event processing and callback execution.

    Warnings:
        When overriding methods, always call the parent implementation using super().

    Usage:
        Derived classes must implement the `execute` method to define their core logic.
        The `setup` method can be optionally overridden to perform initialization
        before the execution begins.

    Attributes:
        config (BaseAgentConfig): Configuration parameters that define the agent's behavior.
        plugin (PluginProtocol): Plugin interface for agent extension.
        state_events (StateEvents): Events for internal state management.
        control_events (ControlEvents): Events for external command handling.

    Methods:
        run: Main entry point for agent execution.
        setup: Performs initialization when the agent starts.
        execute: Implements the agent's core logic.
        stop: Requests external termination of the agent.
        validate_config: Validates the configuration.
        on_stop: Handles cleanup when the agent is stopped.
    """

    a_type: str = ""

    Config = AgentConfig
    Plugin = AgentPlugin

    class StateEvents:
        """
        Events related to the internal state of the agent.

        Attributes:
            start_event: Event to signal that the agent is starting.
            ready_event: Event to signal that the agent is ready to start the execution.
            close_event: Event to signal that the agent has completed the execution.
        """

        def __init__(self, start_event, ready_event, close_event):
            self.start_event = start_event
            self.ready_event = ready_event
            self.close_event = close_event

    class ControlEvents:
        """
        Events related to external commands.

        Attributes:
            setup_event: Event to signal that the agent can make the setup.
            execute_event: Event to signal that the agent can make the execution.
            stop_event: Event to signal that the agent must stop.
        """

        def __init__(self, setup_event, execute_event, stop_event):
            self.setup_event = setup_event
            self.execute_event = execute_event
            self.stop_event = stop_event

    def __init__(
        self,
        name: Optional[str] = None,
        config: Optional[AgentConfig] = None,
        plugin: Optional[AgentPlugin] = None,
        a_type: Literal["process", "thread"] = "process",
        control_events: Optional[ControlEvents] = None,
        state_events: Optional[StateEvents] = None,
        msg_channel: Optional[MessageChannel] = None,
        **kwargs,
    ):
        """
        Creates an agent with the specified configuration and event handlers.
        The agent can be identified by its name in logs and uses events to
        manage its lifecycle and respond to external commands. The agent type
        determines whether it will run as a process or thread.

        The agent's behavior is defined by two types of events:

        - State events track the agent's internal state transitions
        - Control events handle external commands and execution flow

        Events are communicated to the orchestrator via message channel,
        allowing centralized event management and coordination.

        Additional keyword arguments are automatically stored as instance
        attributes, allowing for flexible extension of the agent's properties.

        Args:
            name (str | None): The agent name.
            config (BaseAgentConfig): The agent configuration.
            plugin (BaseAgentPlugin): The plugin interface for agent extension.
            a_type (Literal["process", "thread"]): The agent type.
            control_events (ControlEvents, optional): Events for external command handling.
            state_events (StateEvents, optional): Events for internal state management.
            msg_channel (MessageChannel, optional): Message channel for service communication.
            **kwargs: Additional keyword arguments for agent configuration.
        """
        super().__init__(**kwargs)

        self.config = config if config else self.Config()
        self.plugin = plugin if plugin else self.Plugin()
        self.name = name if name else self.__class__.__name__

        self.start_time = 0
        """Timestamp when the agent started running."""
        self.a_type = a_type
        """The agent type (process or thread)."""
        self.termination_status = AgentTerminationStatus.SUCCESS
        """Agent termination status."""

        EventType = (
            multiprocessing.Event if self.a_type == "process" else threading.Event
        )

        self._validate_agent_class()

        self.state_events = state_events or self.StateEvents(
            start_event=EventType(),
            ready_event=EventType(),
            close_event=EventType(),
        )
        """Events related to the internal state of the agent."""
        self.control_events = control_events or self.ControlEvents(
            setup_event=EventType(),
            execute_event=EventType(),
            stop_event=EventType(),
        )
        """Events related to external commands."""

        if not control_events:
            # default set to ready
            self.control_events.setup_event.set()
            self.control_events.execute_event.set()

        self.plugin_manager = PluginManager(self.plugin)
        """Plugin manager for managing plugins."""
        self.msg_channel = msg_channel or MessageChannel(self.a_type)
        """Message channel for service communication."""

    @final
    def run(self) -> None:
        """
        @final

        Main method to run the agent.

        Warnings:
            Do not override this method. If you need to implement custom logic when the agent is started, you can
            override the `setup` and `execute` methods.

        Notes:
            This method is called by the `run` method of the derived classes. So it can be considered the entry point
            for the agent execution.

        Returns:
            None
        """
        self.start_time = time.time()

        self._handle_start()

        if self.state_events is not None:
            self.state_events.start_event.set()

        self.setup_logger()

        try:
            self._info()

            self.validate_config()

            # Pass agent reference to plugins before initialization
            self.plugin_manager.set_owner(self)

            self.plugin_manager.initialize_plugins()

            self.setup()

            self._handle_ready()

            if self.state_events is not None:
                self.state_events.ready_event.set()

            self.execute()

        except ConfigValidationError as e:
            self.logger.error(f"Agent cannot start due to configuration error.")
            self.termination_status = AgentTerminationStatus.ERROR

        except Exception as ex:
            self.logger.exception(f"[{self.name}] Error during execution: {ex}")
            self.termination_status = AgentTerminationStatus.CRITICAL

            # Send error message to orchestrator
            error_message = ServiceMessage.create_status(
                sender=self.name,
                status="error",
                error=str(ex),
            )
            self.send_message(error_message)

        finally:

            self.on_close()

            self.plugin_manager.finalize_plugins()

            self._handle_stop()

            if self.state_events is not None:
                self.state_events.close_event.set()

            elapsed = time.time() - self.start_time
            self.logger.debug(
                f"Agent lifecycle completed in {elapsed:.3f} seconds with status: {self.termination_status.value}"
            )

    def _handle_start(self):
        """
        Handles initialization when the agent starts.

        Notes:
            Override this method to implement custom initialization logic
            that should execute when the agent starts.

            Events are sent to the orchestrator via message channel
            for centralized event handling.
        """
        msg = ServiceMessage.create_status(
            sender=self.name,
            status="success",
            event_name=AgentEvent.AGENT_START.value,
        )
        self.send_message(msg)

    def _handle_stop(self):
        """
        Handles cleanup when the agent is stopped.

        Events are sent to the orchestrator via message channel
        for centralized event handling.
        """
        msg = ServiceMessage.create_status(
            sender=self.name,
            status="success",
            event_name=AgentEvent.AGENT_CLOSE.value,
        )
        self.send_message(msg)

    def _handle_ready(self):
        """
        Handles the agent's readiness state.

        Events are sent to the orchestrator via message channel
        for centralized event handling.
        """
        msg = ServiceMessage.create_status(
            sender=self.name,
            status="success",
            event_name=AgentEvent.AGENT_READY.value,
        )
        self.send_message(msg)

    def setup(self):
        """
        @template

        Performs initialization when the agent starts.

        Warnings:
            When overriding, ensure to call the parent implementation.

        Notes:
            Implement setup logic here. This method runs once before `execute`.

            - Uses `control_events.setup_event` for execution control.
            - Triggers `state_events.ready_event` upon completion.
        """
        if self.control_events is not None:
            self.control_events.setup_event.wait()

    @abstractmethod
    def execute(self):
        """
        @abstractmethod
        Implements the agent's core logic.

        Warnings:
            When overriding, ensure to call the parent implementation.
        """
        if self.control_events is not None:
            self.control_events.execute_event.wait()

    @final
    def stop(self):
        """
        @final

        Method to request the external stop of the agent.

        Notes:
            If you need to implement custom logic when the agent is being stopped, you can override the `on_stop` method.

        Warnings:
            Do not override this method.
        """
        self.on_stop()
        self.control_events.stop_event.set()

    def on_stop(self):
        """
        Handles cleanup when the agent is stopped.

        Notes:
            Override this method to implement custom cleanup logic
            that should execute when the agent is stopped.
        """
        pass

    def on_close(self):
        """
        Performs final cleanup when the agent is closing.

        Notes:
            Override this method to implement custom cleanup logic
            that should execute during agent shutdown.
        """

    def _info(self) -> None:
        """
        Logs the agent configuration details.

        Returns:
            None
        """
        self.logger.debug(f"Config: logger_level: {self.config.logger_config.level}")

    def _validate_agent_class(self):
        """
        Validates self to ensure it has a valid 'a_type' attribute.

        Raises:
            ValueError: If the agent class does not have a valid 'a_type' attribute.
        """
        if not hasattr(self, "a_type") or self.a_type not in [
            "process",
            "thread",
        ]:
            raise ValueError(
                "Invalid agent type. Ensure the agent class has a valid 'a_type' attribute set to 'process' or 'thread'."
            )

    def send_message(self, msg: ServiceMessage) -> None:
        """
        Sends a message to the orchestrator.

        Args:
            msg (ServiceMessage): The message to send.
        """
        self.msg_channel.send("orchestrator", msg)

    def on_message(self, msg: ServiceMessage) -> None:
        """
        React to orchestrator commands.

        Args:
            msg (ServiceMessage): The received message.
        """
        pass


class BaseProcessAgent(BaseAgent, multiprocessing.Process, ABC):
    """
    BaseProcessAgent class.

    This class provides a common interface for agents that run in a separate process.

    Args:
        BaseAgent (_type_): BaseAgent class.
        multiprocessing (_type_): multiprocessing module.
        ABC (_type_): ABC module.
    """

    a_type: str = "process"

    def __init__(self, name: str | None = None, **kwargs):
        """
        BaseProcessAgent constructor.

        Args:
            name: The agent name.
        """
        multiprocessing.Process.__init__(self, name=name)
        BaseAgent.__init__(self, name=name, a_type="process", **kwargs)


class BaseThreadAgent(BaseAgent, threading.Thread, ABC):
    """
    BaseThreadAgent class.

    Args:
        BaseAgent (_type_): BaseAgent class.
        threading (_type_): threading module.
        ABC (_type_): ABC module."
    """

    a_type: str = "thread"

    def __init__(self, name: str | None = None, **kwargs):
        """
        BaseThreadAgent constructor.

        Args:
            name: The agent name.
        """
        threading.Thread.__init__(self, name=name)
        BaseAgent.__init__(self, name=name, a_type="thread", **kwargs)


class AgentProtocol(Protocol):
    """
    Protocol defining the required interface for agent implementations.

    This protocol specifies the methods and attributes that any agent
    implementation must provide.
    """

    a_type: str
    name: str
    daemon: bool
    ident: int | None
    pid: int | None
    termination_status: AgentTerminationStatus
    config: AgentConfig
    plugin: BaseClass.Plugin
    plugin_manager: PluginManager
    state_events: BaseAgent.StateEvents
    control_events: BaseAgent.ControlEvents
    start_time: float
    # plugins: dict[str, BaseClass.Plugin]

    def run(self) -> None: ...

    def setup(self) -> None: ...

    def execute(self) -> None: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def join(self) -> None: ...

    def is_alive(self) -> bool: ...

    def validate_config(self) -> None: ...

    def on_stop(self) -> None: ...
