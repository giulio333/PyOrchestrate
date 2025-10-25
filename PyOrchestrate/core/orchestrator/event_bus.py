"""
Orchestrator Event Bus.

This module provides the OrchestratorEventBus class that wraps EventManager and EventStore
to provide a unified interface for event emission and history tracking. It automatically
records events to the event store when they are emitted, simplifying event management.
"""

from typing import List, Optional, Callable

from PyOrchestrate.core.utilities.event_manager import EventManager
from PyOrchestrate.core.orchestrator.event_store import EventStore, EventRecord
from PyOrchestrate.core.utilities.event import OrchestratorEvent


class OrchestratorEventBus:
    """
    Centralized event system with automatic history tracking.

    The OrchestratorEventBus combines EventManager (for callbacks) and EventStore
    (for history) into a single, unified interface. When events are emitted, they
    are automatically tracked to the event store, eliminating the need for manual
    history recording.

    This class provides:
    - Event callback registration via EventManager
    - Automatic event history tracking to EventStore
    - Query API for event history analysis
    - Unified interface for all event operations

    Example:
        ```python
        event_store = EventStore(capacity=1000)
        event_bus = OrchestratorEventBus(event_store)

        # Register callback
        event_bus.register_callback(
            OrchestratorEvent.AGENT_STARTED,
            lambda agent_name: print(f"Agent {agent_name} started")
        )

        # Emit event (automatically tracked to history)
        event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent1")

        # Query history
        history = event_bus.get_history(agent_name="agent1")
        ```

    Thread Safety:
        Both EventManager and EventStore are thread-safe, making this class
        safe for use in multi-threaded environments.
    """

    def __init__(self, event_store: EventStore):
        """
        Initialize the event bus.

        Args:
            event_store: EventStore instance for history tracking
        """
        self.event_manager = EventManager()
        self.event_store = event_store

    def register_callback(
        self, event_type: OrchestratorEvent, callback: Callable
    ) -> None:
        """
        Register a callback for a specific event type.

        The callback will be invoked whenever the event is emitted. Callbacks
        receive event data as keyword arguments.

        Args:
            event_type: The orchestrator event to listen for
            callback: Function to call when event occurs (receives event data as kwargs)

        Example:
            ```python
            def on_agent_ready(agent_name: str, **kwargs):
                print(f"Agent {agent_name} is ready")

            event_bus.register_callback(
                OrchestratorEvent.AGENT_READY,
                on_agent_ready
            )
            ```
        """
        self.event_manager.register_event(event_type, callback)

    def emit(self, event_type: OrchestratorEvent, **kwargs) -> None:
        """
        Emit an event and automatically track it to history.

        This method performs two operations:
        1. Emits the event to all registered callbacks via EventManager
        2. Records the event to EventStore for history tracking

        Args:
            event_type: The orchestrator event to emit
            **kwargs: Event data passed to callbacks and stored in history

        Example:
            ```python
            event_bus.emit(
                OrchestratorEvent.AGENT_ERROR,
                agent_name="agent1",
                error_message="Connection failed"
            )
            ```
        """
        # Emit to registered callbacks
        self.event_manager.emit(event_type, **kwargs)

        # Determine severity based on event type
        severity = "ERROR" if event_type == OrchestratorEvent.AGENT_ERROR else "INFO"

        # Track to history
        self.event_store.record(
            category="orchestrator",
            event_name=event_type.value,
            agent=kwargs.get("agent_name"),
            severity=severity,
            data={k: str(v) for k, v in kwargs.items() if k != "agent_name"},
        )

    def get_history(
        self,
        agent_name: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[EventRecord]:
        """
        Query event history.

        Returns a list of event records matching the specified filters.
        If no filters are provided, returns all events.

        Args:
            agent_name: Filter by agent name (optional)
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return (default: 100)

        Returns:
            List[EventRecord]: List of matching event records

        Example:
            ```python
            # Get all events for specific agent
            agent_events = event_bus.get_history(agent_name="agent1")

            # Get last 10 error events
            errors = event_bus.get_history(
                event_type="agent_error",
                limit=10
            )
            ```
        """
        return self.event_store.last(n=limit, agent=agent_name, event_name=event_type)

    def get_agent_timeline(
        self, agent_name: str, limit: int = 100
    ) -> List[EventRecord]:
        """
        Get complete event timeline for a specific agent.

        Returns all events related to the specified agent in chronological order.

        Args:
            agent_name: Name of the agent
            limit: Maximum number of events to return (default: 100)

        Returns:
            List[EventRecord]: Chronological list of events for the agent

        Example:
            ```python
            timeline = event_bus.get_agent_timeline("agent1")
            for event in timeline:
                print(f"{event.timestamp}: {event.event_name}")
            ```
        """
        return self.event_store.last(n=limit, agent=agent_name)

    def get_stats(self, agent_name: Optional[str] = None) -> dict:
        """
        Get event statistics.

        Returns statistics about recorded events, optionally filtered by agent.

        Args:
            agent_name: Agent name to filter statistics (optional)

        Returns:
            dict: Statistics dictionary with event counts

        Example:
            ```python
            # Global statistics
            global_stats = event_bus.get_stats()

            # Agent-specific statistics
            agent_stats = event_bus.get_stats(agent_name="agent1")
            ```
        """
        return self.event_store.stats(agent=agent_name)

    def shutdown(self) -> None:
        """
        Shutdown the event bus.

        Stops the EventManager's executor and prevents new event emissions.
        Call this method during orchestrator shutdown to ensure clean termination.

        Example:
            ```python
            # During orchestrator shutdown
            event_bus.shutdown()
            ```
        """
        self.event_manager.shutdown()
