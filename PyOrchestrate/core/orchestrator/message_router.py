"""Generation-aware routing of agent messages to orchestrator events."""

import threading
from typing import TYPE_CHECKING, Optional, Set

from PyOrchestrate.core.utilities.event import AgentEvent, OrchestratorEvent
from PyOrchestrate.core.utilities.messaging import MessageChannel, ServiceMessage

if TYPE_CHECKING:
    from loguru import Logger

    from PyOrchestrate.core.orchestrator.channel_handler import ChannelHandler
    from PyOrchestrate.core.orchestrator.event_bus import OrchestratorEventBus


class MessageRouter:
    """Route only messages belonging to an agent's active generation."""

    def __init__(
        self,
        event_bus: "OrchestratorEventBus",
        message_channel: MessageChannel,
        logger: "Logger",
    ):
        # The bus, not the bare EventManager: routed lifecycle events must
        # reach EventStore as well as the registered callbacks.
        self.event_bus = event_bus
        self.message_channel = message_channel
        self.logger = logger
        self._active_generations: dict[str, int] = {}
        self._terminated_generations: set[tuple[str, int | None]] = set()
        self._generation_lock = threading.Lock()
        self._channel_handler: Optional["ChannelHandler"] = None

    def start(self) -> None:
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
        if self._channel_handler is None:
            self.logger.debug("MessageRouter not started, nothing to stop")
            return
        self._channel_handler.stop(timeout=timeout)
        self._channel_handler = None
        self.logger.debug("MessageRouter stopped")

    def is_running(self) -> bool:
        return self._channel_handler is not None

    def activate_generation(self, agent_name: str, generation_id: int) -> None:
        """Make one generation authoritative before its instance starts."""
        with self._generation_lock:
            self._active_generations[agent_name] = generation_id
            self._terminated_generations = {
                record
                for record in self._terminated_generations
                if record[0] != agent_name
            }

    def _accepts(self, agent_name: str, generation_id: int | None) -> bool:
        with self._generation_lock:
            active = self._active_generations.get(agent_name)
            if active is None:
                # Preserve compatibility for external/legacy producers until
                # the lifecycle manager has activated a generation.
                return True
            return generation_id == active

    def route_agent_message(self, msg: ServiceMessage) -> None:
        """Filter stale generations before interpreting any status event."""
        self.logger.debug(f"Received {msg}: {msg.payload.get('event')}")
        if msg.type != "STATUS":
            self.logger.warning(f"Ignoring non-STATUS message type: {msg.type}")
            return

        generation_id = msg.payload.get("generation_id")
        if not self._accepts(msg.sender, generation_id):
            self.logger.debug(
                f"Ignoring stale message from agent '{msg.sender}' "
                f"generation {generation_id}."
            )
            return

        event = msg.payload.get("event")
        if event == AgentEvent.AGENT_CLOSE.value:
            self.mark_agent_terminated(msg.sender, generation_id)
            self.event_bus.emit(
                OrchestratorEvent.AGENT_TERMINATED, agent_name=msg.sender
            )
        elif event == AgentEvent.AGENT_START.value:
            self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name=msg.sender)
        elif event == AgentEvent.AGENT_READY.value:
            self.event_bus.emit(OrchestratorEvent.AGENT_READY, agent_name=msg.sender)
        elif event == AgentEvent.AGENT_HEARTBEAT.value:
            if not self.is_agent_terminated(msg.sender, generation_id):
                self.event_bus.emit(
                    OrchestratorEvent.AGENT_HEARTBEAT, agent_name=msg.sender
                )
        elif event in {AgentEvent.AGENT_ERROR.value, "ERROR"}:
            error_msg = msg.payload.get("message") or msg.payload.get(
                "error", "Unknown error"
            )
            self.logger.error(f"Agent {msg.sender} reported error: {error_msg}")
            self.event_bus.emit(
                OrchestratorEvent.AGENT_ERROR,
                agent_name=msg.sender,
                error_message=error_msg,
            )
        else:
            self.logger.warning(f"Unknown agent event: {event}")

    def mark_agent_terminated(
        self, agent_name: str, generation_id: int | None = None
    ) -> None:
        """Mark only the matching active generation as terminated."""
        with self._generation_lock:
            active = self._active_generations.get(agent_name)
            if active is not None:
                if generation_id is not None and generation_id != active:
                    return
                generation_id = active
            self._terminated_generations.add((agent_name, generation_id))

    def is_agent_terminated(
        self, agent_name: str, generation_id: int | None = None
    ) -> bool:
        with self._generation_lock:
            active = self._active_generations.get(agent_name)
            if generation_id is None and active is not None:
                generation_id = active
            return (agent_name, generation_id) in self._terminated_generations

    def reset_termination_state(self, agent_name: str) -> None:
        """Compatibility helper; new starts should use ``activate_generation``."""
        with self._generation_lock:
            active = self._active_generations.get(agent_name)
            self._terminated_generations.discard((agent_name, active))
            self._terminated_generations.discard((agent_name, None))

    def get_terminated_agents(self) -> Set[str]:
        """Return names whose active generation is terminated."""
        with self._generation_lock:
            return {
                name
                for name, generation in self._terminated_generations
                if self._active_generations.get(name, generation) == generation
            }
