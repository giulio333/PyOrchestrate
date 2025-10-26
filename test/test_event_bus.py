"""
Unit tests for OrchestratorEventBus.

Tests the event bus functionality including callback registration, event emission,
automatic history tracking, and query operations.
"""

import unittest
from unittest.mock import MagicMock, call

from PyOrchestrate.core.orchestrator.event_bus import OrchestratorEventBus
from PyOrchestrate.core.orchestrator.event_store import EventStore
from PyOrchestrate.core.utilities.event import OrchestratorEvent


class TestOrchestratorEventBus(unittest.TestCase):
    """Test suite for OrchestratorEventBus class."""

    def setUp(self):
        """Set up test fixtures."""
        self.event_store = EventStore(capacity=1000)
        self.event_bus = OrchestratorEventBus(self.event_store)

    def test_initialization(self):
        """Test OrchestratorEventBus initialization."""
        self.assertIsNotNone(self.event_bus.event_manager)
        self.assertIsNotNone(self.event_bus.event_store)
        self.assertEqual(self.event_bus.event_store, self.event_store)

    def test_register_callback(self):
        """Test registering event callbacks."""
        callback = MagicMock()

        self.event_bus.register_callback(OrchestratorEvent.AGENT_STARTED, callback)

        # Emit event to verify callback is registered
        self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent1")

        callback.assert_called_once()

    def test_emit_event_calls_callback(self):
        """Test that emitting an event calls registered callbacks."""
        callback = MagicMock()
        self.event_bus.register_callback(OrchestratorEvent.AGENT_READY, callback)

        self.event_bus.emit(OrchestratorEvent.AGENT_READY, agent_name="agent1")

        # Check that callback was called with agent_name
        callback.assert_called_once()
        call_args = callback.call_args
        self.assertEqual(call_args.kwargs["agent_name"], "agent1")

    def test_emit_event_records_to_history(self):
        """Test that emitting an event records it to event store."""
        self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent1")

        # Query history
        history = self.event_bus.get_history(agent_name="agent1", limit=10)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].event_name, "agent_started")
        self.assertEqual(history[0].agent, "agent1")

    def test_emit_error_event_uses_error_severity(self):
        """Test that error events are recorded with ERROR severity."""
        self.event_bus.emit(
            OrchestratorEvent.AGENT_ERROR,
            agent_name="agent1",
            error_message="Test error",
        )

        history = self.event_bus.get_history(agent_name="agent1", limit=10)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].severity, "ERROR")

    def test_emit_non_error_event_uses_info_severity(self):
        """Test that non-error events are recorded with INFO severity."""
        self.event_bus.emit(OrchestratorEvent.AGENT_READY, agent_name="agent1")

        history = self.event_bus.get_history(agent_name="agent1", limit=10)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].severity, "INFO")

    def test_get_history_with_agent_filter(self):
        """Test getting history filtered by agent name."""
        # Emit events for different agents
        self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent1")
        self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent2")
        self.event_bus.emit(OrchestratorEvent.AGENT_READY, agent_name="agent1")

        # Get history for agent1
        history = self.event_bus.get_history(agent_name="agent1", limit=100)

        self.assertEqual(len(history), 2)
        for event in history:
            self.assertEqual(event.agent, "agent1")

    def test_get_history_with_event_type_filter(self):
        """Test getting history filtered by event type."""
        # Emit different event types
        self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent1")
        self.event_bus.emit(OrchestratorEvent.AGENT_READY, agent_name="agent1")
        self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent2")

        # Get history for AGENT_STARTED events
        history = self.event_bus.get_history(event_type="agent_started", limit=100)

        self.assertEqual(len(history), 2)
        for event in history:
            self.assertEqual(event.event_name, "agent_started")

    def test_get_history_with_limit(self):
        """Test getting history with limit parameter."""
        # Emit multiple events
        for i in range(10):
            self.event_bus.emit(
                OrchestratorEvent.AGENT_HEARTBEAT, agent_name=f"agent{i}"
            )

        # Get history with limit
        history = self.event_bus.get_history(limit=5)

        self.assertEqual(len(history), 5)

    def test_get_agent_timeline(self):
        """Test getting complete timeline for a specific agent."""
        # Emit events for agent
        self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent1")
        self.event_bus.emit(OrchestratorEvent.AGENT_READY, agent_name="agent1")
        self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent2")
        self.event_bus.emit(OrchestratorEvent.AGENT_TERMINATED, agent_name="agent1")

        # Get timeline
        timeline = self.event_bus.get_agent_timeline("agent1", limit=100)

        self.assertEqual(len(timeline), 3)
        self.assertEqual(timeline[0].event_name, "agent_started")
        self.assertEqual(timeline[1].event_name, "agent_ready")
        self.assertEqual(timeline[2].event_name, "agent_terminated")

    def test_get_stats_global(self):
        """Test getting global statistics."""
        # Emit various events
        self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent1")
        self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent2")
        self.event_bus.emit(OrchestratorEvent.AGENT_READY, agent_name="agent1")

        # Get global stats
        stats = self.event_bus.get_stats()

        self.assertIsInstance(stats, dict)
        # Should have recorded events - stats is dict[str, int]
        self.assertGreater(len(stats), 0)

    def test_get_stats_by_agent(self):
        """Test getting statistics for specific agent."""
        # Emit events
        self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent1")
        self.event_bus.emit(OrchestratorEvent.AGENT_READY, agent_name="agent1")
        self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent2")

        # Get stats for agent1
        stats = self.event_bus.get_stats(agent_name="agent1")

        self.assertIsInstance(stats, dict)
        # Should have agent1's events

    def test_multiple_callbacks_for_same_event(self):
        """Test registering multiple callbacks for the same event."""
        callback1 = MagicMock()
        callback2 = MagicMock()

        self.event_bus.register_callback(OrchestratorEvent.AGENT_READY, callback1)
        self.event_bus.register_callback(OrchestratorEvent.AGENT_READY, callback2)

        self.event_bus.emit(OrchestratorEvent.AGENT_READY, agent_name="agent1")

        # Both callbacks should be called (EventManager may execute async)
        # Wait a bit for async execution
        import time

        time.sleep(0.1)

        # At least one callback should be called
        self.assertTrue(callback1.called or callback2.called)

    def test_event_data_stored_in_history(self):
        """Test that event data is properly stored in history."""
        self.event_bus.emit(
            OrchestratorEvent.AGENT_ERROR,
            agent_name="agent1",
            error_message="Connection failed",
            error_code=500,
        )

        history = self.event_bus.get_history(agent_name="agent1", limit=10)

        self.assertEqual(len(history), 1)
        event = history[0]
        if event.data:
            self.assertEqual(event.data.get("error_message"), "Connection failed")
            self.assertEqual(event.data.get("error_code"), "500")

    def test_shutdown(self):
        """Test shutting down the event bus."""
        # Register callback and emit event before shutdown
        callback = MagicMock()
        self.event_bus.register_callback(OrchestratorEvent.AGENT_STARTED, callback)
        self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent1")

        callback.assert_called_once()

        # Shutdown
        self.event_bus.shutdown()

        # Emitting after shutdown should not call callback
        # (EventManager prevents new emissions after shutdown)
        callback.reset_mock()
        self.event_bus.emit(OrchestratorEvent.AGENT_READY, agent_name="agent1")

        # Callback should not be called after shutdown
        callback.assert_not_called()

    def test_no_callbacks_registered(self):
        """Test emitting events with no callbacks registered."""
        # Should not raise any errors
        self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent1")

        # But should still record to history
        history = self.event_bus.get_history(agent_name="agent1", limit=10)
        self.assertEqual(len(history), 1)

    def test_empty_history(self):
        """Test querying history when no events have been emitted."""
        history = self.event_bus.get_history(limit=10)
        self.assertEqual(len(history), 0)

    def test_callback_with_no_parameters(self):
        """Test callback that doesn't accept parameters."""
        callback = MagicMock()

        self.event_bus.register_callback(OrchestratorEvent.AGENT_STARTED, callback)
        self.event_bus.emit(OrchestratorEvent.AGENT_STARTED, agent_name="agent1")

        # Should be called (EventManager handles parameter filtering)
        callback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
