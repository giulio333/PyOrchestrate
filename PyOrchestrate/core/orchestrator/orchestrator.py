import time
from typing import List, final, Optional
from enum import Enum

from PyOrchestrate.core.agent.base_agent import BaseAgent
from PyOrchestrate.core.orchestrator.memory import OMemory, AgentEntry
from PyOrchestrate.core.orchestrator.dependency_graph import DependencyGraph
from PyOrchestrate.core.orchestrator.lifecycle_manager import AgentLifecycleManager
from PyOrchestrate.core.orchestrator.worker_pool import WorkerPoolScheduler
from PyOrchestrate.core.orchestrator.message_router import MessageRouter
from PyOrchestrate.core.orchestrator.event_bus import OrchestratorEventBus
from PyOrchestrate.core.orchestrator.command_interface import CommandInterface
from PyOrchestrate.core.orchestrator.event_store import EventStore, BucketRingStore
from PyOrchestrate.core.utilities.event import OrchestratorEvent
from PyOrchestrate.core.utilities.validation import (
    ValidationResult,
    ValidationSeverity,
    ConfigValidationError,
)

from PyOrchestrate.core.base.base import BaseClass
from PyOrchestrate.core.utilities.messaging import MessageChannel, ServiceMessage
from PyOrchestrate.core.plugins.plugin_manager import PluginManager
from PyOrchestrate.core.plugins.heartbeat import (
    OrchestratorHeartbeatPlugin,
)


class RunMode(Enum):
    """
    Execution mode for the Orchestrator main loop.

    **When to use STOP_ON_EMPTY:**
    - Batch processing jobs with defined end
    - ETL pipelines
    - One-time data migrations
    - Testing scenarios

    **When to use DAEMON:**
    - Web servers and APIs
    - Continuous monitoring systems
    - Event-driven architectures
    - Long-running services requiring CLI control

    **Important:** DAEMON mode requires explicit shutdown via CLI
    command 'shutdown' or programmatic call to stop().
    """

    STOP_ON_EMPTY = "stop_on_empty"
    """Stop when all agents finished"""
    DAEMON = "daemon"
    """Keep running until explicitly shutdown"""


class OrchestratorConfig(BaseClass.Config):
    """
    Orchestrator configuration class.

    Attributes:
        check_interval (float): The interval to check the agents. Defaults to 1.
        max_workers (int): The maximum number of workers that can run concurrently. Defaults to 5.
        agent_start_timeout (float): Maximum time in seconds to wait for an agent to start. Defaults to 30.0.
        agent_stop_timeout (float): Maximum time in seconds to wait for agents to terminate during shutdown. Defaults to 10.0.
        enable_command_interface (bool): Enable external command interface via ZeroMQ over TCP. Defaults to True.
        command_zmq_address (str): ZeroMQ address for external commands. Defaults to ``"tcp://*:5555"``.
        logger (LoggerConfig): Logger configuration.
        run_mode (RunMode): Required lifecycle policy. Defaults to RunMode.STOP_ON_EMPTY.
        history_max_events (int): Maximum number of events to store in history (ring buffer size). Defaults to 5000.
        history_payload_bytes (int): Maximum size for event payload data. Defaults to 256.
    """

    check_interval: float = 1
    """The interval to check the agents."""
    max_workers: int = 5
    """The maximum number of workers that can run concurrently."""
    agent_start_timeout: float = 30.0
    """Maximum time in seconds to wait for an agent to start. Defaults to 30.0."""
    agent_stop_timeout: float = 10.0
    """Maximum time in seconds to wait for agents to terminate during shutdown."""
    enable_command_interface: bool = True
    """Enable external command interface via ZeroMQ."""
    command_zmq_address: str = "tcp://*:5555"
    """ZeroMQ address for external commands."""
    allowed_commands: set[str] | str | None = None
    """Allowed commands for CLI interface. Can be a set of commands, a preset name, or None for all commands."""
    run_mode: RunMode = RunMode.STOP_ON_EMPTY
    """Execution mode for the orchestrator. Defaults to RunMode.STOP_ON_EMPTY."""
    history_max_events: int = 5000
    """Maximum number of events to store in history (ring buffer size)."""
    history_payload_bytes: int = 256
    """Maximum size for event payload data."""

    def __init__(
        self,
        check_interval: float | None = None,
        max_workers: int | None = None,
        agent_start_timeout: float | None = None,
        agent_stop_timeout: float | None = None,
        enable_command_interface: bool | None = None,
        command_zmq_address: str | None = None,
        allowed_commands: set[str] | str | None = None,
        run_mode: RunMode | None = None,
        history_max_events: int | None = None,
        history_payload_bytes: int | None = None,
        **kwargs,
    ):
        """
        Initialize the OrchestratorConfig.

        Args:
            check_interval (float | None, optional): The interval to check the agents. Defaults to None.
            max_workers (int | None, optional): The maximum number of workers that can run concurrently. Defaults to None.
            agent_start_timeout (float | None, optional): Maximum time in seconds to wait for an agent to start. Defaults to None.
            agent_stop_timeout (float | None, optional): Maximum time in seconds to wait for agents to terminate during shutdown. Defaults to None.
            enable_command_interface (bool | None, optional): Enable external command interface via ZeroMQ. Defaults to None.
            command_zmq_address (str | None, optional): ZeroMQ address for external commands. Defaults to None.
            allowed_commands (set[str] | str | None, optional): Allowed commands for CLI interface. Can be a set of commands, a preset name, or None for all commands. Defaults to None.
            run_mode (RunMode | None, optional): Execution mode for the orchestrator. If None, defaults to RunMode.STOP_ON_EMPTY
                (stops when all agents finish).
            history_max_events (int | None, optional): Maximum number of events to store in history (ring buffer size). Defaults to None.
            history_payload_bytes (int | None, optional): Maximum size for event payload data. Defaults to None.
        """
        super().__init__(**kwargs)

        if check_interval is not None:
            self.check_interval = check_interval

        if max_workers is not None:
            self.max_workers = max_workers

        if agent_start_timeout is not None:
            self.agent_start_timeout = agent_start_timeout

        if agent_stop_timeout is not None:
            self.agent_stop_timeout = agent_stop_timeout

        if enable_command_interface is not None:
            self.enable_command_interface = enable_command_interface

        if command_zmq_address is not None:
            self.command_zmq_address = command_zmq_address

        if allowed_commands is not None:
            self.allowed_commands = allowed_commands

        if run_mode is not None:
            self.run_mode = run_mode

        if history_max_events is not None:
            self.history_max_events = history_max_events

        if history_payload_bytes is not None:
            self.history_payload_bytes = history_payload_bytes

    def validate(self) -> List[ValidationResult]:
        results = super().validate()

        if self.check_interval <= 0:
            results.append(
                ValidationResult(
                    field="check_interval",
                    message="check_interval must be greater than 0.",
                    severity=ValidationSeverity.ERROR,
                )
            )

        if self.max_workers <= 0:
            results.append(
                ValidationResult(
                    field="max_workers",
                    message="max_workers must be greater than 0.",
                    severity=ValidationSeverity.ERROR,
                )
            )

        if self.agent_start_timeout <= 0:
            results.append(
                ValidationResult(
                    field="agent_start_timeout",
                    message="agent_start_timeout must be greater than 0.",
                    severity=ValidationSeverity.ERROR,
                )
            )

        if self.agent_stop_timeout <= 0:
            results.append(
                ValidationResult(
                    field="agent_stop_timeout",
                    message="agent_stop_timeout must be greater than 0.",
                    severity=ValidationSeverity.ERROR,
                )
            )

        if self.enable_command_interface and not self.command_zmq_address:
            results.append(
                ValidationResult(
                    field="command_zmq_address",
                    message="command_zmq_address must be specified when enable_command_interface is True.",
                    severity=ValidationSeverity.ERROR,
                )
            )

        if getattr(self, "run_mode", None) is None or not isinstance(
            self.run_mode, RunMode
        ):
            results.append(
                ValidationResult(
                    field="run_mode",
                    message="run_mode is required and must be one of RunMode.STOP_ON_EMPTY or RunMode.DAEMON.",
                    severity=ValidationSeverity.ERROR,
                )
            )

        if self.history_max_events <= 0:
            results.append(
                ValidationResult(
                    field="history_max_events",
                    message="history_max_events must be greater than 0.",
                    severity=ValidationSeverity.ERROR,
                )
            )

        if self.history_payload_bytes <= 0:
            results.append(
                ValidationResult(
                    field="history_payload_bytes",
                    message="history_payload_bytes must be greater than 0.",
                    severity=ValidationSeverity.ERROR,
                )
            )

        return results


class OrchestratorPlugin(BaseClass.Plugin):
    """
    Plugin class for the Orchestrator.

    This class can contain various plugins that extend orchestrator functionality.

    Plugins can be defined as class attributes (defaults) and overridden via constructor:

    Example:
        class MyOrchestratorPlugin(OrchestratorPlugin):
            custom_plugin = CustomPlugin()

        # Use default
        plugin1 = MyOrchestratorPlugin()

        # Override heartbeat
        plugin2 = MyOrchestratorPlugin(heartbeat=OrchestratorHeartbeatPlugin())
    """

    heartbeat: OrchestratorHeartbeatPlugin | None = None


class Orchestrator(BaseClass):
    """
    Orchestrator class to manages the agents.

    The Orchestrator provides centralized event management and coordination for all agents.
    Agents communicate with the orchestrator via message channels, and the orchestrator
    handles all event processing and callback execution through its own event manager.

    This centralized approach eliminates event duplication and provides a single point
    of control for system-wide event handling.

    Attributes:
        memory (OMemory): Memory to store the agents.
        event_manager (EventManager): Centralized event manager for handling all agent events.
        dependencies (dict[str, list[str]]): Dependencies among agents.

    """

    Config = OrchestratorConfig
    Plugin = OrchestratorPlugin

    config: OrchestratorConfig
    plugin: OrchestratorPlugin

    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        plugin: Optional[OrchestratorPlugin] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.config = config if config else self.Config()
        self.plugin = plugin if plugin else self.Plugin()
        self.name = name if name else self.__class__.__name__

        self.setup_logger()
        self._info()

        self.validate_config()

        self.memory = OMemory()
        self.msg_channel = MessageChannel("process")

        # Event store for history tracking
        event_store = EventStore(
            capacity=self.config.history_max_events,
            payload_max_bytes=self.config.history_payload_bytes,
            event_policies={
                OrchestratorEvent.AGENT_HEARTBEAT.value: BucketRingStore(2)
            },
        )

        # Event bus combines EventManager + EventStore with automatic history tracking
        self.event_bus = OrchestratorEventBus(event_store)

        # Initialize specialized managers
        self.dependency_graph = DependencyGraph()

        self.lifecycle_manager = AgentLifecycleManager(
            self.memory, self.config, self.logger
        )

        self.worker_pool = WorkerPoolScheduler(
            self.config.max_workers, self.lifecycle_manager, self.logger
        )

        # Message router for agent message handling (manages its own ChannelHandler)
        self.message_router = MessageRouter(
            self.event_bus, self.msg_channel, self.logger
        )
        self.lifecycle_manager.before_start = self.message_router.activate_generation

        # Initialize plugin manager for centralized plugin management
        self.plugin_manager = PluginManager(self.plugin)
        self.plugin_manager.set_owner(self)
        self.plugin_manager.plugin_info()

        # Initialize orchestrator plugins
        self.plugin_manager.initialize_plugins()

        # Command interface for external CLI commands
        self.command_interface: Optional[CommandInterface] = None
        if self.config.enable_command_interface:
            self.command_interface = CommandInterface(
                orchestrator=self,
                zmq_address=self.config.command_zmq_address,
                allowed_commands=self.config.allowed_commands,
                event_store=event_store,
                logger=self.logger,
            )

        self._shutdown_requested = False
        """Flag for graceful shutdown via CLI"""

        # Record orchestrator initialization event
        self.event_bus.event_store.record(
            category="orchestrator",
            event_name="INIT",
            severity="INFO",
            data={"run_mode": self.config.run_mode.value},
        )

        # Start channel handlers for agent messages and external commands
        self._setup_channel_handlers()

    def _setup_channel_handlers(self):
        """
        Initialize and start message channel handlers.

        Starts MessageRouter for agent messages and CommandInterface for
        external commands (if enabled).
        """
        # Message router (always enabled) - manages its own ChannelHandler
        self.message_router.start()

        # Command interface (conditionally enabled)
        if self.command_interface:
            self.command_interface.start()

    def _shutdown_channel_handlers(self):
        """
        Stop all channel handlers gracefully.

        Stops the message router and command interface (if enabled),
        waiting for their threads to terminate properly.
        """
        self.message_router.stop(timeout=2.0)

        if self.command_interface:
            self.command_interface.stop(timeout=2.0)

    def register_agent(
        self,
        agent_class,
        name: str,
        custom_config: BaseClass.Config | None = None,
        custom_plugin: BaseClass.Plugin | None = None,
        control_events: BaseAgent.ControlEvents | None = None,
        state_events: BaseAgent.StateEvents | None = None,
        msg_channel: MessageChannel | None = None,
        **kwargs,
    ) -> AgentEntry:
        """
        Register an agent on the orchestrator.

        Notes:
            After registering the agent, you can call the `start` method to start all agents.

            Events from agents are handled centrally by the orchestrator's event manager.
            Agents communicate with the orchestrator via message channel.

            Delegates to AgentLifecycleManager.

        Warnings:
            agent_name must be unique.

        Args:
            agent_class: Class of the agent to register.
            name: Name of the agent.
            custom_config: Custom configuration for the agent.
            custom_plugin: Custom plugin for the agent.
            control_events: Control events for the agent.
            state_events: State events for the agent.
            msg_channel: Message channel for the agent.
            kwargs: Additional arguments for the agent.

        Returns:
            AgentEntry: The agent entry object stored in the memory.

        Raises:
            ValueError: If an agent with the same name is already registered.
            Exception: If agent registration fails for any reason.
        """

        try:
            # Auto-inject heartbeat plugin if exists
            heartbeat_plugin = self.plugin_manager.get_plugin("heartbeat")
            if heartbeat_plugin:
                assert isinstance(heartbeat_plugin, OrchestratorHeartbeatPlugin)
                custom_plugin = heartbeat_plugin.inject_agent_heartbeat_plugin(
                    custom_plugin
                )

            # Register via lifecycle manager
            agent_entry: AgentEntry = self.lifecycle_manager.register_agent(
                agent_class=agent_class,
                name=name,
                custom_config=custom_config,
                custom_plugin=custom_plugin,
                control_events=control_events,
                state_events=state_events,
                msg_channel=msg_channel or self.msg_channel,
                **kwargs,
            )

            # Emit registration event
            self.event_bus.emit(OrchestratorEvent.AGENT_REGISTERED, agent_name=name)

            return agent_entry

        except Exception as e:
            self.logger.error(f"Failed to register agent '{name}': {e}")
            raise

    def register_event(self, event_type, callback):
        """
        Register a callback function for a specific event type.

        Args:
            event_type: The type of event to listen for (e.g., OrchestratorEvent.AGENT_STARTED).
            callback: The callback function to execute when the event occurs.
                     The callback will receive the event data as arguments.

        Example:
            orchestrator.register_event(OrchestratorEvent.AGENT_STARTED, on_agent_start)
            orchestrator.register_event(OrchestratorEvent.AGENT_TERMINATED, on_agent_terminated)
        """
        self.event_bus.register_callback(event_type, callback)
        self.logger.debug(f"Event callback registered for event type: {event_type}")

    def add_dependency(self, agent_name: str, depends_on: list[str]):
        """
        Add dependencies: agent_name depends on depends_on.

        Validation is performed during validate_dependencies() call.
        Delegates entirely to DependencyGraph.

        Args:
            agent_name: Name of the agent that has dependencies
            depends_on: List of agent names that agent_name depends on
        """
        self.dependency_graph.add_dependency(agent_name, depends_on)
        self.logger.info(f"Agent '{agent_name}' depends on {depends_on}.")

    def validate_dependencies(self):
        """
        Validate dependency graph for errors (cycles, missing agents).

        Delegates entirely to DependencyGraph.

        Raises:
            ValueError: If validation fails (cycles or unregistered agents)
        """
        agent_names = {agent.name for agent in self.memory.agents}
        self.dependency_graph.validate(agent_names)

    def start(self):
        """
        Start all registered agents in the topological order of their dependencies.

        Delegates to WorkerPoolScheduler for agent startup.
        """

        self.start_time = time.time()

        self.validate_dependencies()

        # Get topologically sorted agent order (dependencies first)
        agent_names = {agent.name for agent in self.memory.agents}
        ordered_agents = self.dependency_graph.topological_sort(agent_names)

        # Start agents via worker pool scheduler
        for agent_name in ordered_agents:
            self.worker_pool.start_agent(agent_name)

    def stop(self):
        """
        Terminates all registered agents.

        Cancels queued starts and delegates running-agent stops to
        AgentLifecycleManager through WorkerPoolScheduler.
        """
        self.worker_pool.stop_all()

    def join(self) -> None:
        """
        Check the status of all agents and wait for them to complete.

        Notes:
            This method blocks the current thread until all agents are terminated.

            If command interface is enabled, the orchestrator will continue running
            even after all agents have finished, allowing remote control via CLI.
            Use the 'shutdown' command to terminate the orchestrator in this mode.

            - When agent is terminated, it emits an `OrchestratorEvent.AGENT_TERMINATED` event.

            Uses WorkerPoolScheduler to manage agent termination and queue.

            Once the loop exits, every agent is stopped and joined within
            `agent_stop_timeout` before channel handlers and plugins are shut
            down. A process agent that ignores the cooperative stop request is
            force-terminated; a thread agent that ignores it cannot be, so it
            is quarantined and reported.
        """

        all_finished: bool = False

        while self._should_continue_running(all_finished):
            alive_count = 0

            for agent in self.memory.agents:
                # A prepared generation may already have an instance but not
                # have called Thread/Process.start() yet. Startup owns the slot
                # until it publishes its typed result.
                if self.worker_pool.is_starting(agent.name):
                    continue

                if not agent.is_initialized:
                    continue

                if not agent.is_alive():
                    if self.worker_pool.tracks_agent(agent.name):
                        self.logger.info(f"Agent '{agent.name}' ended.")
                        self.worker_pool.on_agent_terminated(agent.name)
                        self.message_router.mark_agent_terminated(
                            agent.name, agent.generation_id
                        )
                else:
                    alive_count += 1

            # Check if all agents finished via worker pool
            all_finished = self.worker_pool.all_finished

            time.sleep(self.config.check_interval)

        self.logger.info("Orchestrator is shutting down...")

        # Agents must be gone before the router and the plugins are torn down,
        # otherwise they keep running against closed channels.
        survivors = self.worker_pool.shutdown_all(
            timeout=self.config.agent_stop_timeout
        )
        if survivors:
            self.logger.critical(
                f"Agents still alive after shutdown: {', '.join(survivors)}"
            )

        # Track orchestrator shutdown
        self.event_bus.event_store.record(
            category="orchestrator",
            event_name="SHUTDOWN",
            severity="INFO",
            data={
                "total_agents": str(len(self.memory.agents)),
                "surviving_agents": str(len(survivors)),
            },
        )

        # Stop all channel handlers
        self._shutdown_channel_handlers()

        # Finalize plugins
        self.plugin_manager.finalize_plugins()

        self.logger.debug(f"elapsed: {time.time() - self.start_time}")

    def _should_continue_running(self, all_finished: bool) -> bool:
        """Decide whether the main join loop should continue based on run_mode.

        Notes:
            - DAEMON: keep running until shutdown requested.
            - STOP_ON_EMPTY: stop when all agents have finished.
        """
        rm = self.config.run_mode
        if rm == RunMode.DAEMON:
            return not self._shutdown_requested
        # Default enforced by validation: STOP_ON_EMPTY
        return not all_finished

    def simple_join(self) -> None:
        """
        Simple join method to wait for all processes or threads to complete their execution.
        """
        for agent in self.memory.agents:
            self.lifecycle_manager.join_agent(agent.name)
        self.logger.info("All processes or threads have terminated.")

        self.logger.debug(f"elapsed: {time.time() - self.start_time}")

    def report(self):
        """Report the status of all agents."""
        self.logger.info(f"Reporting {len(self.memory.agents)} agents status.")
        for agent in self.memory.agents:
            self.logger.info(agent.status())

    def _info(self):
        self.logger.debug(f"Config: check_interval={self.config.check_interval}")
        self.logger.debug(f"Config: max_workers={self.config.max_workers}")
        self.logger.debug(
            f"Config: agent_start_timeout={self.config.agent_start_timeout}"
        )
        self.logger.debug(
            f"Config: enable_command_interface={self.config.enable_command_interface}"
        )
        if self.config.enable_command_interface:
            self.logger.debug(
                f"Config: command_zmq_address={self.config.command_zmq_address}"
            )
            # Log allowed commands information
            if self.config.allowed_commands is None:
                self.logger.debug("Config: allowed_commands=ALL (no restrictions)")
            elif isinstance(self.config.allowed_commands, str):
                self.logger.debug(
                    f"Config: allowed_commands={self.config.allowed_commands} (preset)"
                )
            elif isinstance(self.config.allowed_commands, set):
                self.logger.debug(
                    f"Config: allowed_commands={sorted(self.config.allowed_commands)} (custom)"
                )
        # Log run_mode explicitly (mandatory)
        rm = getattr(self.config, "run_mode", None)
        if isinstance(rm, RunMode):
            self.logger.debug(f"Config: run_mode={rm.value}")
        else:
            self.logger.debug(f"Config: run_mode={rm}")
