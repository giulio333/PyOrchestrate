"""
Message Router for Orchestrator.

This module provides the MessageRouter class that handles routing of agent messages
to the orchestrator event system. It includes thread-safe tracking of terminated agents
to filter stale messages (e.g., heartbeats from agents that have already terminated).
"""

import threading
from typing import Set, Optional, TYPE_CHECKING

from PyOrchestrate.core.utilities.messaging import ServiceMessage, MessageChannel
from PyOrchestrate.core.utilities.event import OrchestratorEvent, AgentEvent
from PyOrchestrate.core.utilities.event_manager import EventManager

if TYPE_CHECKING:
    from loguru import Logger
    from PyOrchestrate.core.orchestrator.channel_handler import ChannelHandler


class MessageRouter:
    """
    Routes messages from agents to orchestrator event system.

    The MessageRouter is responsible for:
    - Converting agent STATUS messages to orchestrator events
    - Filtering stale heartbeat messages from terminated agents
    - Thread-safe tracking of agent termination states
    - Emitting events to registered callbacks via EventManager

    This class isolates message routing logic from the main Orchestrator,
    making it easier to test and maintain.

    Example:
        ```python
        event_manager = EventManager()
        router = MessageRouter(event_manager, logger)

        # Process incoming agent message
        router.route_agent_message(service_message)

        # Mark agent as terminated
        router.mark_agent_terminated("agent_name")
        ```

    Thread Safety:
        All methods that access `_terminated_agents` are thread-safe and can be
        called from multiple threads concurrently.
    """

    def __init__(
        self,
        event_manager: EventManager,
        message_channel: MessageChannel,
        logger: "Logger",
    ):
        """
        Initialize the message router.

        Args:
            event_manager: EventManager instance for emitting orchestrator events
            message_channel: MessageChannel for receiving agent messages
            logger: Logger instance (typically loguru logger)
        """
        self.event_manager = event_manager
        self.message_channel = message_channel
        self.logger = logger
        self._terminated_agents: Set[str] = set()
        self._terminated_agents_lock = threading.Lock()
        self._channel_handler: Optional["ChannelHandler"] = None

    def start(self) -> None:
        """
        Start the message router and its channel handler.

        Creates and starts a ChannelHandler to process incoming agent messages.
        """
        # Import here to avoid circular dependency at runtime
        from PyOrchestrate.core.orchestrator.channel_handler import ChannelHandler

        if self._channel_handler is not None:
            self.logger.warning("MessageRouter already started")
            return

        self._channel_handler = ChannelHandler(
            channel=self.message_channel,
            message_handler=self.route_agent_message,
            name="OrchestratorAgentMessageHandler",
            logger=self.logger,
            poll_timeout=1.0,
        )
        self._channel_handler.start()
        self.logger.debug("MessageRouter started")

    def stop(self, timeout: float = 2.0) -> None:
        """
        Stop the message router and its channel handler.

        Args:
            timeout: Maximum time to wait for handler thread to stop
        """
        if self._channel_handler is None:
            self.logger.debug("MessageRouter not started, nothing to stop")
            return

        self._channel_handler.stop(timeout=timeout)
        self._channel_handler = None
        self.logger.debug("MessageRouter stopped")

    def is_running(self) -> bool:
        """
        Check if the message router is currently running.

        Returns:
            bool: True if running, False otherwise
        """
        return self._channel_handler is not None

    def route_agent_message(self, msg: ServiceMessage) -> None:
        """
        Process and route a message from an agent.

        Converts agent STATUS messages to orchestrator events.
        Filters stale heartbeat messages from terminated agents.

        Only STATUS messages are processed. Other message types are ignored
        with a warning log entry.

        Args:
            msg: The service message from an agent

        Notes:
            - AGENT_CLOSE: Marks agent as terminated and emits AGENT_TERMINATED event
            - AGENT_START: Emits AGENT_STARTED event
            - AGENT_READY: Emits AGENT_READY event
            - AGENT_HEARTBEAT: Emits AGENT_HEARTBEAT event (filtered if agent terminated)
            - ERROR: Emits AGENT_ERROR event with error message
        """
        self.logger.debug(f"Received {msg}: {msg.payload.get('event')}")

        if msg.type != "STATUS":
            self.logger.warning(f"Ignoring non-STATUS message type: {msg.type}")
            return

        event = msg.payload.get("event")

        if event == AgentEvent.AGENT_CLOSE.value:
            # Mark agent as terminated to filter out stale heartbeat messages
            self.mark_agent_terminated(msg.sender)
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
            if not self.is_agent_terminated(msg.sender):
                self.event_manager.emit(
                    OrchestratorEvent.AGENT_HEARTBEAT, agent_name=msg.sender
                )
            else:
                self.logger.debug(
                    f"Ignoring stale heartbeat from terminated agent '{msg.sender}'"
                )
        elif event == "ERROR":
            error_msg = msg.payload.get("message") or msg.payload.get(
                "error", "Unknown error"
            )
            self.logger.error(f"Agent {msg.sender} reported error: {error_msg}")
            self.event_manager.emit(
                OrchestratorEvent.AGENT_ERROR,
                agent_name=msg.sender,
                error_message=error_msg,
            )
        else:
            self.logger.warning(f"Unknown agent event: {event}")

    def mark_agent_terminated(self, agent_name: str) -> None:
        """
        Mark an agent as terminated to filter future stale messages.

        This is a thread-safe operation that updates the internal set of
        terminated agents. Once marked, heartbeat messages from this agent
        will be filtered out.

        Args:
            agent_name: Name of the terminated agent
        """
        with self._terminated_agents_lock:
            self._terminated_agents.add(agent_name)

    def is_agent_terminated(self, agent_name: str) -> bool:
        """
        Check if an agent has been marked as terminated.

        This is a thread-safe operation that checks the internal set of
        terminated agents.

        Args:
            agent_name: Name of the agent to check

        Returns:
            bool: True if agent is terminated, False otherwise
        """
        with self._terminated_agents_lock:
            return agent_name in self._terminated_agents

    def reset_termination_state(self, agent_name: str) -> None:
        """
        Reset termination state for an agent.

        This is useful for scenarios where an agent might be restarted
        and should no longer be considered terminated.

        Args:
            agent_name: Name of the agent
        """
        with self._terminated_agents_lock:
            self._terminated_agents.discard(agent_name)

    def get_terminated_agents(self) -> Set[str]:
        """
        Get a copy of the set of terminated agents.

        Returns:
            Set[str]: Copy of terminated agents set (thread-safe)
        """
        with self._terminated_agents_lock:
            return self._terminated_agents.copy()
