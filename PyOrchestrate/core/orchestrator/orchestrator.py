import time
import threading
import json
from collections import defaultdict, deque
from typing import List, final

from PyOrchestrate.core.agent.base_agent import BaseAgent
from PyOrchestrate.core.orchestrator.memory import OMemory, AgentEntry
from PyOrchestrate.core.utilities.event_manager import EventManager
from PyOrchestrate.core.utilities.event import OrchestratorEvent, AgentEvent
from PyOrchestrate.core.utilities.validation import (
    ValidationPolicy,
    ValidationResult,
    ValidationSeverity,
    ConfigValidationError,
)

from PyOrchestrate.core.base.base import BaseClass
from PyOrchestrate.core.utilities.validation import ValidationResult
from PyOrchestrate.core.utilities.messaging import MessageChannel, ServiceMessage
from PyOrchestrate.core.utilities.command_handler import CommandHandler


class OrchestratorConfig(BaseClass.Config):
    """
    Orchestrator configuration class.

    Attributes:
        check_interval (float): The interval to check the agents.
        max_workers (int): The maximum number of workers that can run concurrently.
        enable_command_interface (bool): Enable external command interface via UNIX socket.
        command_socket_path (str): Path to the UNIX socket for external commands.
        logger (LoggerConfig): Logger configuration.
    """

    check_interval: float = 1
    """The interval to check the agents."""
    max_workers: int = 5
    """The maximum number of workers that can run concurrently."""
    enable_command_interface: bool = False
    """Enable external command interface via UNIX socket."""
    command_socket_path: str = "/tmp/pyorchestrate.sock"
    """Path to the UNIX socket for external commands."""

    def __init__(
        self,
        check_interval: float | None = None,
        max_workers: int | None = None,
        enable_command_interface: bool | None = None,
        command_socket_path: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if check_interval is not None:
            self.check_interval = check_interval

        if max_workers is not None:
            self.max_workers = max_workers

        if enable_command_interface is not None:
            self.enable_command_interface = enable_command_interface

        if command_socket_path is not None:
            self.command_socket_path = command_socket_path

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
        return results


class OrchestratorPlugin(BaseClass.Plugin):
    pass


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

    def __init__(
        self,
        config: BaseClass.Config | None = None,
        plugin: BaseClass.Plugin | None = None,
        name: str | None = None,
    ):
        super().__init__(
            name=name or self.__class__.__name__,
            config=config or Orchestrator.Config(),
            plugin=plugin or Orchestrator.Plugin(),
        )

        self.setup_logger()
        self._info()

        self.validate_config()

        self.memory = OMemory()
        self.event_manager = EventManager()
        self.msg_channel = MessageChannel("process")

        # Command interface for external CLI commands
        self.command_channel = None
        if self.config.enable_command_interface:
            self.command_channel = MessageChannel(
                "unix_socket", self.config.command_socket_path
            )
            self.command_handler = CommandHandler(self)
            self.logger.debug(
                f"Command interface enabled on socket: {self.config.command_socket_path}"
            )

        self.dependencies: dict[str, list[str]] = defaultdict(list)
        self._running_agents = 0
        self._waiting_agents_queue = deque()  # Queue for waiting agents
        self._started_agents = set()  # Set for agents that have been started
        self._shutdown_requested = False  # Flag for graceful shutdown via CLI

        # Flag to control the execution of the message thread
        self._message_thread_running = False
        self._message_thread = None
        # Start the thread to check messages
        self._start_message_thread()

    def _message_thread_function(self):
        """
        Function executed in a separate thread to continuously check
        for incoming messages in the queue.
        """
        self.logger.trace("Message handling thread started")
        while self._message_thread_running:
            try:
                # Check if there are messages in the queue from agents
                msg = self.msg_channel.receive(timeout=0.5)
                if msg:
                    self.handle_agent_message(msg)

                # Check if there are external commands (if command interface is enabled)
                if self.command_channel:
                    cmd_msg = self.command_channel.receive(timeout=0.5)
                    if cmd_msg:
                        self.handle_external_command(cmd_msg)

            except Exception as e:
                self.logger.error(f"Error in message handling thread: {e}")

            # Short pause to avoid excessive CPU usage
            time.sleep(0.01)

        self.logger.trace("Message handling thread terminated")

    def _start_message_thread(self):
        """
        Start a separate thread to handle incoming messages.
        """
        if self._message_thread_running:
            return

        self._message_thread_running = True
        self._message_thread = threading.Thread(
            target=self._message_thread_function,
            daemon=True,  # The thread will terminate when the main thread terminates
            name="OrchestratorMessageThread",
        )
        self._message_thread.start()
        self.logger.debug("Message handling thread started successfully")

    def _stop_message_thread(self):
        """
        Stop the message handling thread.
        """
        if not self._message_thread_running:
            return

        self._message_thread_running = False
        if self._message_thread:
            self._message_thread.join(timeout=2.0)  # Wait at most 2 seconds
            if self._message_thread.is_alive():
                self.logger.warning("The message handling thread did not stop properly")
            else:
                self.logger.trace("Message handling thread stopped successfully")
            self._message_thread = None

    def handle_agent_message(self, msg: ServiceMessage) -> None:
        """
        Process a single message coming from an agent.

        Notes:
            Only messages of type 'STATUS' are processed and relayed to the orchestrator's `EventManager`.
        """
        self.logger.debug(
            f"Received message from {msg.sender}: {msg.type} - {msg.payload}"
        )

        if msg.type == "STATUS":
            if msg.payload == AgentEvent.AGENT_CLOSE.value:
                self.event_manager.emit(
                    OrchestratorEvent.AGENT_TERMINATED, agent_name=msg.sender
                )
            elif msg.payload == AgentEvent.AGENT_START.value:
                self.event_manager.emit(
                    OrchestratorEvent.AGENT_STARTED, agent_name=msg.sender
                )
            elif msg.payload == AgentEvent.AGENT_READY.value:
                self.event_manager.emit(
                    OrchestratorEvent.AGENT_READY, agent_name=msg.sender
                )
            elif msg.payload.startswith("ERROR:"):
                error_msg = msg.payload[6:]  # Remove "ERROR:" prefix
                self.logger.error(f"Agent {msg.sender} reported error: {error_msg}")
                self.event_manager.emit(
                    OrchestratorEvent.AGENT_ERROR,
                    agent_name=msg.sender,
                    error_message=error_msg,
                )

    def handle_external_command(self, msg: ServiceMessage) -> None:
        """Process external commands from CLI."""
        # self.logger.debug(f"Received external command from {msg.sender}: {msg.payload}")

        try:
            import json
            from datetime import datetime

            cmd_data = json.loads(msg.payload)
            command = cmd_data.get("command")
            args = cmd_data.get("args", [])

            # Delegate command execution to the command handler
            if self.command_handler:
                response = self.command_handler.execute_command(command, args)
            else:
                response = {
                    "status": "error",
                    "message": "Command interface not enabled",
                }

            # Send response back through the command channel
            if self.command_channel:
                self.command_channel.send(
                    "cli",
                    ServiceMessage(
                        sender="orchestrator",
                        type="STATUS",
                        payload=json.dumps(response),
                        timestamp=datetime.now(),
                    ),
                )

        except Exception as e:
            self.logger.error(f"Error processing external command: {e}")
            error_response = {"status": "error", "message": str(e)}
            if self.command_channel:
                self.command_channel.send(
                    "cli",
                    ServiceMessage(
                        sender="orchestrator",
                        type="STATUS",
                        payload=json.dumps(error_response),
                        timestamp=datetime.now(),
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
        self._shutdown_requested = not self.config.enable_command_interface

        while not all_finished and not self._shutdown_requested:
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
                if not self.config.enable_command_interface:
                    all_finished = True
            else:
                time.sleep(self.config.check_interval)

        self.logger.info("Orchestrator is shutting down...")

        # Stop the message handling thread
        self._stop_message_thread()

        # Close command channel if enabled
        if self.command_channel:
            self.command_channel.close()
            self.logger.debug("Command interface closed")

        self.logger.debug(f"elapsed: {time.time() - self.start_time}")

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
