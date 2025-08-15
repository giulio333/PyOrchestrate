"""
Test cases for Event History functionality

Tests the EventStore class and integration with Orchestrator.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from PyOrchestrate.core.orchestrator.event_store import EventStore, EventRecord
from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator, RunMode
from PyOrchestrate.core.agent import PeriodicProcessAgent


class TestEventStore:
    """Test the EventStore class functionality."""

    def test_event_store_initialization(self):
        """Test EventStore initializes with correct defaults."""
        store = EventStore()
        assert store._events.maxlen == 5000
        assert store._payload_max == 256
        assert store._seq == 0
        assert len(store._events) == 0

    def test_event_store_custom_capacity(self):
        """Test EventStore with custom capacity."""
        store = EventStore(capacity=100, payload_max_bytes=64)
        assert store._events.maxlen == 100
        assert store._payload_max == 64

    def test_record_basic_event(self):
        """Test recording a basic event."""
        store = EventStore()

        store.record(
            category="test",
            type="TEST_EVENT",
            agent="test-agent",
            severity="INFO",
            data={"key": "value"},
        )

        assert len(store._events) == 1
        assert store._seq == 1

        event = store._events[0]
        assert event.seq == 1
        assert event.category == "test"
        assert event.type == "TEST_EVENT"
        assert event.agent == "test-agent"
        assert event.severity == "INFO"
        assert event.data == {"key": "value"}

    def test_record_truncation(self):
        """Test payload truncation."""
        store = EventStore(payload_max_bytes=10)

        long_text = "a" * 20
        store.record(category="test", type="TEST_EVENT", data={"long": long_text})

        event = store._events[0]
        assert len(event.data["long"]) == 10
        assert event.data["long"].endswith("...")

    def test_eventrecord_to_dict_and_json(self):
        """Verify EventRecord.to_dict() and to_json() shapes and values."""
        store = EventStore()
        store.record(
            category="test",
            type="TYPE_X",
            agent="agent-1",
            severity="WARN",
            data={"k": "v"},
        )

        event = store._events[0]
        d = event.to_dict()

        # Basic keys
        assert d["seq"] == event.seq
        assert "timestamp" in d and isinstance(d["timestamp"], str)
        assert d["category"] == "test"
        assert d["type"] == "TYPE_X"
        assert d["agent"] == "agent-1"
        assert d["data"]["k"] == "v"

        # JSON serialization returns a valid JSON string
        j = event.to_json()
        assert isinstance(j, str)
        import json as _json

        parsed = _json.loads(j)
        assert parsed["seq"] == event.seq

    def test_ring_buffer_behavior(self):
        """Test ring buffer capacity limits."""
        store = EventStore(capacity=3)

        # Add 5 events
        for i in range(5):
            store.record(category="test", type=f"EVENT_{i}")

        # Should only keep last 3
        assert len(store._events) == 3
        assert store._seq == 5  # Sequence continues counting

        # Check we have events 2, 3, 4
        seqs = [e.seq for e in store._events]
        assert seqs == [3, 4, 5]

    def test_query_last_events(self):
        """Test querying last N events."""
        store = EventStore()

        # Add multiple events
        for i in range(10):
            store.record(
                category="test",
                type="TEST_EVENT",
                agent=f"agent-{i % 3}",
                data={"index": str(i)},
            )

        # Test basic last query
        events = store.last(5)
        assert len(events) == 5
        assert [e.seq for e in events] == [6, 7, 8, 9, 10]

    def test_query_filtered_by_agent(self):
        """Test filtering events by agent."""
        store = EventStore()

        # Add events for different agents
        for i in range(10):
            store.record(category="test", type="TEST_EVENT", agent=f"agent-{i % 3}")

        # Filter by specific agent
        agent_events = store.last(agent="agent-1")
        assert len(agent_events) > 0
        assert all(e.agent == "agent-1" for e in agent_events)

    def test_query_filtered_by_type(self):
        """Test filtering events by type."""
        store = EventStore()

        # Add events of different types
        for i in range(10):
            store.record(category="test", type=f"TYPE_{i % 3}")

        # Filter by specific type
        type_events = store.last(type="TYPE_1")
        assert len(type_events) > 0
        assert all(e.type == "TYPE_1" for e in type_events)

    def test_query_after_sequence(self):
        """Test filtering events after sequence number."""
        store = EventStore()

        # Add 10 events
        for i in range(10):
            store.record(category="test", type="TEST_EVENT")

        # Get events after sequence 5
        events = store.last(after_seq=5)
        assert len(events) == 5
        assert all(e.seq > 5 for e in events)

    def test_stats_global(self):
        """Test global statistics."""
        store = EventStore()

        # Add events of different types
        for i in range(5):
            store.record(category="test", type="TYPE_A")
        for i in range(3):
            store.record(category="test", type="TYPE_B")

        stats = store.stats()
        assert stats["by_type"]["TYPE_A"] == 5
        assert stats["by_type"]["TYPE_B"] == 3

    def test_stats_by_agent(self):
        """Test statistics filtered by agent."""
        store = EventStore()

        # Add events for different agents and types
        for i in range(3):
            store.record(category="test", type="TYPE_A", agent="agent-1")
        for i in range(2):
            store.record(category="test", type="TYPE_B", agent="agent-1")
        for i in range(4):
            store.record(category="test", type="TYPE_A", agent="agent-2")

        # Check agent-1 stats
        agent1_stats = store.stats(agent="agent-1")
        assert agent1_stats["by_type"]["TYPE_A"] == 3
        assert agent1_stats["by_type"]["TYPE_B"] == 2

        # Check agent-2 stats
        agent2_stats = store.stats(agent="agent-2")
        assert agent2_stats["by_type"]["TYPE_A"] == 4
        assert "TYPE_B" not in agent2_stats["by_type"]

    def test_capacity_info(self):
        """Test capacity information."""
        store = EventStore(capacity=100)

        # Add some events
        for i in range(10):
            store.record(category="test", type="TEST_EVENT")

        info = store.get_capacity_info()
        assert info["capacity"] == 100
        assert info["current_size"] == 10
        assert info["total_events"] == 10
        assert info["oldest_seq"] == 1
        assert info["newest_seq"] == 10

    def test_thread_safety(self):
        """Test thread safety of EventStore."""
        store = EventStore()
        errors = []

        def worker(worker_id):
            try:
                for i in range(100):
                    store.record(
                        category="test",
                        type="CONCURRENT_EVENT",
                        agent=f"worker-{worker_id}",
                        data={"iteration": str(i)},
                    )
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Check no errors occurred
        assert len(errors) == 0
        assert store._seq == 500  # 5 workers * 100 events each

        # Check all events are properly recorded
        events = store.last(500)
        assert len(events) == 500


class TestOrchestratorEventIntegration:
    """Test EventStore integration with Orchestrator."""

    def test_orchestrator_has_event_store(self):
        """Test that Orchestrator initializes with EventStore."""
        orchestrator = Orchestrator(
            config=Orchestrator.Config(
                run_mode=RunMode.STOP_ON_EMPTY,
                history_max_events=1000,
                history_payload_bytes=512,
            )
        )

        assert hasattr(orchestrator, "event_store")
        assert isinstance(orchestrator.event_store, EventStore)
        assert orchestrator.event_store._events.maxlen == 1000
        assert orchestrator.event_store._payload_max == 512

    def test_orchestrator_records_init_event(self):
        """Test that Orchestrator records initialization event."""
        orchestrator = Orchestrator(
            config=Orchestrator.Config(run_mode=RunMode.STOP_ON_EMPTY)
        )

        # Check that INIT event was recorded
        events = orchestrator.event_store.last()
        init_events = [e for e in events if e.type == "INIT"]
        assert len(init_events) == 1
        assert init_events[0].category == "orchestrator"
        assert init_events[0].data is not None
        assert init_events[0].data["run_mode"] == "stop_on_empty"

    def test_event_store_config_validation(self):
        """Test EventStore configuration validation."""
        # Test invalid history_max_events
        with pytest.raises(Exception):  # Should raise validation error
            config = Orchestrator.Config(
                run_mode=RunMode.STOP_ON_EMPTY, history_max_events=0  # Invalid
            )
            config._validate()

        # Test invalid history_payload_bytes
        with pytest.raises(Exception):  # Should raise validation error
            config = Orchestrator.Config(
                run_mode=RunMode.STOP_ON_EMPTY, history_payload_bytes=-1  # Invalid
            )
            config._validate()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
