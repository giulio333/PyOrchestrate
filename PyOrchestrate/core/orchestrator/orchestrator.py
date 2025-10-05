import time
import threading
from collections import defaultdict, deque
from typing import List, final, Optional
from enum import Enum

from PyOrchestrate.core.agent.base_agent import BaseAgent
from PyOrchestrate.core.orchestrator.memory import OMemory, AgentEntry
from PyOrchestrate.core.utilities.command_handler import CommandException
from PyOrchestrate.core.orchestrator.event_store import EventStore, BucketRingStore
from PyOrchestrate.core.utilities.event_manager import EventManager
from PyOrchestrate.core.utilities.event import OrchestratorEvent, AgentEvent
from PyOrchestrate.core.utilities.validation import (
    ValidationResult,
    ValidationSeverity,
    ConfigValidationError,
)

from PyOrchestrate.core.base.base import BaseClass
from PyOrchestrate.core.utilities.validation import ValidationResult
from PyOrchestrate.core.utilities.messaging import MessageChannel, ServiceMessage
from PyOrchestrate.core.plugins.plugin_manager import PluginManager
from PyOrchestrate.core.plugins.heartbeat import (
    OrchestratorHeartbeatPlugin,
)


class RunMode(Enum):
    """
    Execution mode for the Orchestrator main loop.

    Available modes:
    - STOP_ON_EMPTY: Stop when all agents finished
    - DAEMON: Keep running until explicitly shutdown
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
        enable_command_interface (bool): Enable external command interface via UNIX socket. Defaults to True.
        command_socket_path (str): Path to the UNIX socket for external commands. Defaults to "/tmp/pyorchestrate.sock".
        logger (LoggerConfig): Logger configuration.
        run_mode (RunMode): Required lifecycle policy. Defaults to RunMode.STOP_ON_EMPTY.
        history_max_events (int): Maximum number of events to store in history (ring buffer size). Defaults to 5000.
        history_payload_bytes (int): Maximum size for event payload data. Defaults to 256.
    """

    check_interval: float = 1
    """The interval to check the agents."""
    max_workers: int = 5
    """The maximum number of workers that can run concurrently."""
    enable_command_interface: bool = True
    """Enable external command interface via UNIX socket."""
    command_socket_path: str = "/tmp/pyorchestrate.sock"
    """Path to the UNIX socket for external commands."""
    allowed_commands: set[str] | str | None = None
    """Allowed commands for CLI interface. Can be a set of commands, a preset name, or None for all commands."""
    run_mode: RunMode = RunMode.STOP_ON_EMPTY
    """Required explicit run mode. Must be set to RunMode.STOP_ON_EMPTY or RunMode.DAEMON."""
    history_max_events: int = 5000
    """Maximum number of events to store in history (ring buffer size)."""
    history_payload_bytes: int = 256
    """Maximum size for event payload data."""

    def __init__(
        self,
        check_interval: float | None = None,
        max_workers: int | None = None,
        enable_command_interface: bool | None = None,
        command_socket_path: str | None = None,
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
            enable_command_interface (bool | None, optional): Enable external command interface via UNIX socket. Defaults to None.
            command_socket_path (str | None, optional): Path to the UNIX socket for external commands. Defaults to None.
            allowed_commands (set[str] | str | None, optional): Allowed commands for CLI interface. Can be a set of commands, a preset name, or None for all commands. Defaults to None.
            run_mode (RunMode | None, optional): Required lifecycle policy. Must be set to RunMode.STOP_ON_EMPTY or RunMode.DAEMON. Defaults to None.
            history_max_events (int | None, optional): Maximum number of events to store in history (ring buffer size). Defaults to None.
            history_payload_bytes (int | None, optional): Maximum size for event payload data. Defaults to None.
        """
        super().__init__(**kwargs)

        if check_interval is not None:
            self.check_interval = check_interval

        if max_workers is not None:
            self.max_workers = max_workers

        if enable_command_interface is not None:
            self.enable_command_interface = enable_command_interface

        if command_socket_path is not None:
            self.command_socket_path = command_socket_path

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

        if self.enable_command_interface and not self.command_socket_path:
            results.append(
                ValidationResult(
                    field="command_socket_path",
                    message="command_socket_path must be specified when enable_command_interface is True.",
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
    """

    heartbeat: OrchestratorHeartbeatPlugin | None = None

    def __init__(self, heartbeat: OrchestratorHeartbeatPlugin | None = None, **kwargs):
        super().__init__(**kwargs)

        if heartbeat is not None:
            self.heartbeat = heartbeat


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

    Methods:
        register_agent: Register an agent on the orchestrator.
        add_dependency: Add dependencies among agents.
        validate_dependencies: Check for dependency errors.
        start: Start all registered agents.
        stop: Stop all registered agents.
        join: Wait for all agents to complete.
        simple_join: Simple join method to wait for all processes or threads to complete their execution.
        report: Report the status of all agents.
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
        self.event_manager = EventManager()
        self.msg_channel = MessageChannel("process")

        # Event store for history tracking
        self.event_store = EventStore(
            capacity=self.config.history_max_events,
            payload_max_bytes=self.config.history_payload_bytes,
            event_policies={
                OrchestratorEvent.AGENT_HEARTBEAT.value: BucketRingStore(2)
            },
        )

        # Initialize plugin manager for centralized plugin management
        self.plugin_manager = PluginManager(self.plugin)
        self.plugin_manager.set_owner(self)
        self.plugin_manager.plugin_info()

        # Initialize orchestrator plugins
        self.plugin_manager.initialize_plugins()

        # Command interface for external CLI commands
        self.command_channel = None
        if self.config.enable_command_interface:
            # Import here to avoid circular imports
            from PyOrchestrate.core.utilities.command_handler import CommandHandler

            self.command_channel = MessageChannel(
                "unix_socket", self.config.command_socket_path
            )
            self.command_handler = CommandHandler(self, self.config.allowed_commands)
            self.logger.debug(
                f"Command interface enabled on socket: {self.config.command_socket_path}"
            )

        self.dependencies: dict[str, list[str]] = defaultdict(list)
        self._running_agents = 0
        self._waiting_agents_queue = deque()  # Queue for waiting agents
        self._started_agents = set()  # Set for agents that have been started
        self._terminated_agents = (
            set()
        )  # Set for agents that have terminated (to filter stale heartbeats)
        self._shutdown_requested = False  # Flag for graceful shutdown via CLI

        # Separate threads for message and command handling
        self._agent_message_thread_running = False
        self._agent_message_thread = None
        self._command_thread_running = False
        self._command_thread = None

        # Register event history hooks
        self._register_history_hooks()

        # Start separate threads for agent messages and external commands
        self._start_agent_message_thread()
        if self.config.enable_command_interface:
            self._start_command_thread()

    def _register_history_hooks(self):
        """Register automatic event history hooks for all orchestrator events."""
        for ev in OrchestratorEvent:

            def _cb(ev=ev, **kw):
                sev = "ERROR" if ev == OrchestratorEvent.AGENT_ERROR else "INFO"
                self.event_store.record(
                    category="orchestrator",
                    event_name=ev.value,
                    agent=kw.get("agent_name"),
                    severity=sev,
                    data={k: str(v) for k, v in kw.items() if k != "agent_name"},
                )

            self.register_event(ev, _cb)

        self.event_store.record(
            category="orchestrator",
            event_name="INIT",
            severity="INFO",
            data={"run_mode": self.config.run_mode.value},
        )

    def _message_channel_thread_function(self):
        """
        Function executed in a separate thread to continuously check
        for incoming agent messages.

        Optimized for high-throughput message processing:
        - Dedicated thread for agent messages (high priority)
        - Uses short timeouts to avoid blocking
        - Processes messages in tight loop without unnecessary delays
        """
        self.logger.trace("Agent message handling thread started")

        while self._agent_message_thread_running:
            try:
                # Check for agent messages
                msg = self.msg_channel.receive(timeout=0.1)
                if msg:
                    self.handle_agent_message(msg)

            except Exception as e:
                self.logger.error(f"Error in agent message handling thread: {e}")

        self.logger.trace("Agent message handling thread terminated")

    def _command_channel_thread_function(self):
        """
        Function executed in a separate thread to continuously check
        for incoming external commands.

        Separate from agent messages to ensure CLI responsiveness:
        - Dedicated thread for command interface
        - Independent of agent message processing
        - Allows concurrent handling of commands and agent events
        """
        self.logger.trace("Command handling thread started")

        while self._command_thread_running:
            try:
                # Check for external commands
                if self.command_channel:
                    cmd_msg = self.command_channel.receive(timeout=0.1)
                    if cmd_msg:
                        self.handle_external_command(cmd_msg)

            except Exception as e:
                self.logger.error(f"Error in command handling thread: {e}")

        self.logger.trace("Command handling thread terminated")

    def _start_agent_message_thread(self):
        """
        Start a separate thread to handle incoming agent messages.
        """
        if self._agent_message_thread_running:
            return

        self._agent_message_thread_running = True
        self._agent_message_thread = threading.Thread(
            target=self._message_channel_thread_function,
            daemon=True,
            name="OrchestratorAgentMessageThread",
        )
        self._agent_message_thread.start()
        self.logger.debug("Agent message handling thread started successfully")

    def _start_command_thread(self):
        """
        Start a separate thread to handle incoming external commands.
        """
        if self._command_thread_running:
            return

        self._command_thread_running = True
        self._command_thread = threading.Thread(
            target=self._command_channel_thread_function,
            daemon=True,
            name="OrchestratorCommandThread",
        )
        self._command_thread.start()
        self.logger.debug("Command handling thread started successfully")

    def _stop_agent_message_thread(self):
        """
        Stop the agent message handling thread.
        """
        if not self._agent_message_thread_running:
            return

        self._agent_message_thread_running = False
        if self._agent_message_thread:
            self._agent_message_thread.join(timeout=2.0)
            if self._agent_message_thread.is_alive():
                self.logger.warning(
                    "The agent message handling thread did not stop properly"
                )
            else:
                self.logger.trace("Agent message handling thread stopped successfully")
            self._agent_message_thread = None

    def _stop_command_thread(self):
        """
        Stop the command handling thread.
        """
        if not self._command_thread_running:
            return

        self._command_thread_running = False
        if self._command_thread:
            self._command_thread.join(timeout=2.0)
            if self._command_thread.is_alive():
                self.logger.warning("The command handling thread did not stop properly")
            else:
                self.logger.trace("Command handling thread stopped successfully")
            self._command_thread = None

    def handle_agent_message(self, msg: ServiceMessage) -> None:
        """
        Process a single message coming from an agent.

        Notes:
            Only messages of type 'STATUS' are processed and relayed to the orchestrator's `EventManager`.
        """
        self.logger.debug(f"Received {msg}: {msg.payload.get('event')}")

        if msg.type == "STATUS":
            event = msg.payload.get("event")

            if event == AgentEvent.AGENT_CLOSE.value:
                # Mark agent as terminated to filter out stale heartbeat messages
                self._terminated_agents.add(msg.sender)
                self.event_manager.emit(
                    OrchestratorEvent.AGENT_TERMINATED, agent_name=msg.sender
                )
            elif event == AgentEvent.AGENT_START.value:
                self.event_manager.emit(
                    OrchestratorEvent.AGENT_STARTED, agent_name=msg.sender
                )
            elif event == AgentEvent.AGENT_READY.value:
                self.event_manager.emit(
                    OrchestratorEvent.AGENT_READY, agent_name=msg.sender
                )
            elif event == AgentEvent.AGENT_HEARTBEAT.value:
                # Ignore heartbeats from terminated agents (stale messages in queue)
                if msg.sender not in self._terminated_agents:
                    self.event_manager.emit(
                        OrchestratorEvent.AGENT_HEARTBEAT, agent_name=msg.sender
                    )
                else:
                    self.logger.debug(
                        f"Ignoring stale heartbeat from terminated agent '{msg.sender}'"
                    )
            elif event == "ERROR":
                error_msg = msg.payload.get("message", "Unknown error")
                self.logger.error(f"Agent {msg.sender} reported error: {error_msg}")
                self.event_manager.emit(
                    OrchestratorEvent.AGENT_ERROR,
                    agent_name=msg.sender,
                    error_message=error_msg,
                )

    def handle_external_command(self, msg: ServiceMessage) -> None:
        """Process external commands from CLI."""
        request_id = None

        try:
            cmd_data = msg.payload  # Now already a dict
            command = cmd_data.get("command")
            args = cmd_data.get("args", [])
            request_id = cmd_data.get("request_id")

            # Ensure command is not None
            if not command:
                raise ValueError("Command is required")

            assert self.command_handler, "Command handler not initialized"

            try:
                # Delegate command execution to the command handler
                response = self.command_handler.execute_command(command, args)
                msg = ServiceMessage.create_command_response(
                    sender="orchestrator",
                    status="success",
                    data=response,
                    request_id=request_id,
                )
            except CommandException as e:
                self.logger.warning(f"Command '{command}' failed: {e}")
                msg = ServiceMessage.create_command_response(
                    sender="orchestrator",
                    status="error",
                    error=str(e),
                    code=e.code,
                    request_id=request_id,
                )

            # Send response back through the command channel
            assert self.command_channel, "Command channel not initialized"
            self.command_channel.send("cli", msg)

        except Exception as e:
            self.logger.error(f"Error processing external command: {e}")

            # Track error
            self.event_store.record(
                category="cli",
                event_name="CLI_ERROR",
                severity="ERROR",
                data={"error": str(e)},
            )

            if self.command_channel:
                self.command_channel.send(
                    "cli",
                    ServiceMessage.create_command_response(
                        sender="orchestrator",
                        status="error",
                        error=str(e),
                        request_id=request_id,
                    ),
                )

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
        """

        # Auto-inject heartbeat plugin if exists
        heartbeat_plugin = self.plugin_manager.get_plugin("heartbeat")
        if heartbeat_plugin:
            assert isinstance(heartbeat_plugin, OrchestratorHeartbeatPlugin)
            custom_plugin = heartbeat_plugin.inject_agent_heartbeat_plugin(
                custom_plugin
            )

        agent_entry: AgentEntry = self.memory.add_agent(
            agent_class=agent_class,
            name=name,
            custom_config=custom_config,
            custom_plugin=custom_plugin,
            control_events=control_events,
            state_events=state_events,
            msg_channel=msg_channel or self.msg_channel,
            **kwargs,
        )

        self.logger.debug(f"Agent '{name}' registered.")
        return agent_entry

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
        self.event_manager.register_event(event_type, callback)
        self.logger.debug(f"Event callback registered for event type: {event_type}")

    def add_dependency(self, agent_name: str, depends_on: list[str]):
        """
        Add dependencies: agent_name depends on depends_on.
        """
        if agent_name not in [agent.name for agent in self.memory.agents]:
            raise ValueError(
                f"Agent {agent_name} is not registered in the Orchestrator."
            )
        for dependency in depends_on:
            if dependency not in [agent.name for agent in self.memory.agents]:
                raise ValueError(
                    f"Dependency {dependency} is not registered in the Orchestrator."
                )
        self.dependencies[agent_name].extend(depends_on)
        self.logger.info(f"Agent '{agent_name}' depends on {depends_on}.")

    def validate_dependencies(self):
        """
        Check for dependency errors (e.g., circular dependencies like A -> B -> A).
        """
        visited = set()
        stack = set()

        agents = list(self.dependencies.keys())

        def visit(node):
            """Visit a node in the graph."""
            if node in stack:
                raise ValueError(
                    f"Detected a dependency cycle: {node} is part of a cycle."
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
                "Cannot obtain a topological ordering: cyclic dependencies detected?"
            )

        return topo_order

    def start(self):
        """
        Start all registered agents in the topological order of their dependencies.
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
            The agent will emit an `OrchestratorEvent.AGENT_STARTED` event through the message channel when it's actually started.
            If the maximum number of workers is reached, the agent is added to the waiting queue.
        """
        agent: AgentEntry = self.memory.get_agent(agent_name)

        agent.initialize_agent()

        if self._running_agents >= self.config.max_workers:
            self.logger.warning(
                f"Max workers limit reached. Adding {agent_name} to waiting queue."
            )
            self._waiting_agents_queue.append(agent_name)

            # Track agent queued event
            self.event_store.record(
                category="orchestrator",
                event_name="QUEUED",
                agent=agent_name,
                severity="WARN",
                data={
                    "running_agents": str(self._running_agents),
                    "max_workers": str(self.config.max_workers),
                },
            )
            return

        agent.start()
        self._running_agents += 1
        self._started_agents.add(agent_name)

        self.logger.info(f"Starting agent {agent_name}...")

    def stop(self):
        """Terminates all registered agents."""
        for agent in self.memory.agents:
            agent.stop()
            self.logger.info(f"Stopping agent '{agent.name}'.")

    def join(self) -> None:
        """
        Check the status of all agents and wait for them to complete.

        Notes:
            This method blocks the current thread until all agents are terminated.

            If command interface is enabled, the orchestrator will continue running
            even after all agents have finished, allowing remote control via CLI.
            Use the 'shutdown' command to terminate the orchestrator in this mode.

            - When agent is terminated, it emits an `OrchestratorEvent.AGENT_TERMINATED` event.
        """

        all_finished: bool = False

        while self._should_continue_running(all_finished):
            alive_count = 0

            for agent in self.memory.agents:
                if not agent.instance.is_alive():
                    # Check if the agent was started before decrementing
                    if agent.name in self._started_agents:
                        self.logger.info(f"Agent '{agent.name}' ended.")
                        self._running_agents -= 1
                        self._started_agents.remove(agent.name)

                        # Start an agent from the waiting queue if available
                        self._start_waiting_agent()
                else:
                    alive_count += 1

            if alive_count == 0 and not self._waiting_agents_queue:
                all_finished = True

            time.sleep(self.config.check_interval)

        self.logger.info("Orchestrator is shutting down...")

        # Track orchestrator shutdown
        self.event_store.record(
            category="orchestrator",
            event_name="SHUTDOWN",
            severity="INFO",
            data={"total_agents": str(len(self.memory.agents))},
        )

        # Stop both message handling threads
        self._stop_agent_message_thread()
        if self.config.enable_command_interface:
            self._stop_command_thread()

        # Finalize plugins
        self.plugin_manager.finalize_plugins()

        # Close command channel if enabled
        if self.command_channel:
            self.command_channel.close()
            self.logger.debug("Command interface closed")

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

    def _start_waiting_agent(self):
        """
        Start an agent from the waiting queue if available.

        Notes:
            This method is called when an agent terminates, freeing up a slot
            for another waiting agent.
        """
        if not self._waiting_agents_queue:
            return

        if self._running_agents >= self.config.max_workers:
            self.logger.debug(
                f"No slot available to start waiting agents. Running agents: {self._running_agents}, Limit: {self.config.max_workers}"
            )
            return

        agent_name = self._waiting_agents_queue.popleft()
        self.logger.info(
            f"Starting waiting agent {agent_name} from queue... (Running agents: {self._running_agents}, Limit: {self.config.max_workers})"
        )

        # Track agent started from queue
        self.event_store.record(
            category="orchestrator",
            event_name="STARTED_FROM_QUEUE",
            agent=agent_name,
            severity="INFO",
            data={
                "running_agents": str(self._running_agents),
                "max_workers": str(self.config.max_workers),
            },
        )

        agent = self.memory.get_agent(agent_name)
        agent.start()
        self._running_agents += 1
        self._started_agents.add(agent_name)  # Track that the agent has been started

    def simple_join(self) -> None:
        """
        Simple join method to wait for all processes or threads to complete their execution.
        """
        for agent in self.memory.agents:
            agent.join()
        self.logger.info("All processes or threads have terminated.")

        self.logger.debug(f"elapsed: {time.time() - self.start_time}")

    def report(self):
        """Report the status of all agents."""
        self.logger.info(f"Reporting {len(self.memory.agents)} agents status.")
        for agent in self.memory.agents:
            self.logger.info(agent.status())

    @final
    def validate_config(self):
        """
        @final

        Validates the agent configuration.

        Notes:
            This method is called during the agent's initialization to validate the configuration.
            If the configuration is invalid, a `ValidationError` is raised.

        Warning:
            Do not override this method. If you need to implement custom validation logic, override the `validate` method
            in the `Config` class.

        Raises:
            ValidationError: If the configuration is invalid.
        """

        try:
            self.config._validate()
        except ConfigValidationError as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise e
        self.logger.debug(f"Self configuration validated.")

    def _info(self):
        self.logger.debug(f"Config: check_interval={self.config.check_interval}")
        self.logger.debug(f"Config: max_workers={self.config.max_workers}")
        self.logger.debug(
            f"Config: enable_command_interface={self.config.enable_command_interface}"
        )
        if self.config.enable_command_interface:
            self.logger.debug(
                f"Config: command_socket_path={self.config.command_socket_path}"
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
