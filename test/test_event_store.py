"""
Test cases for Event History functionality

Tests the EventStore class and integration with Orchestrator.
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch

from PyOrchestrate.core.orchestrator.event_store import EventStore, EventRecord
from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator, RunMode
from PyOrchestrate.core.agent import PeriodicProcessAgent


class TestEventStore(unittest.TestCase):
    """Test the EventStore class functionality."""

    def test_event_store_initialization(self):
        """Test EventStore initializes with correct defaults."""
        store = EventStore()
        # Test using public interface
        info = store.get_capacity_info()
        global_info = info["global"]
        self.assertIsInstance(global_info, dict)
        capacity_data = global_info["capacity"]
        self.assertIsInstance(capacity_data, dict)
        self.assertEqual(capacity_data["capacity"], 5000)
        self.assertEqual(len(store.last(1)), 0)  # No events recorded yet

    def test_event_store_custom_capacity(self):
        """Test EventStore with custom capacity."""
        store = EventStore(capacity=100, payload_max_bytes=64)
        info = store.get_capacity_info()
        global_info = info["global"]
        self.assertIsInstance(global_info, dict)
        capacity_data = global_info["capacity"]
        self.assertIsInstance(capacity_data, dict)
        self.assertEqual(capacity_data["capacity"], 100)

    def test_record_basic_event(self):
        """Test recording a basic event."""
        store = EventStore()

        store.record(
            category="test",
            event_name="TEST_EVENT",
            agent="test-agent",
            severity="INFO",
            data={"key": "value"},
        )

        events = store.last(1)
        self.assertEqual(len(events), 1)

        event = events[0]
        self.assertEqual(event.seq, 1)
        self.assertEqual(event.category, "test")
        self.assertEqual(event.event_name, "TEST_EVENT")
        self.assertEqual(event.agent, "test-agent")
        self.assertEqual(event.severity, "INFO")
        self.assertEqual(event.data, {"key": "value"})

    def test_record_truncation(self):
        """Test payload truncation."""
        store = EventStore(payload_max_bytes=10)

        long_text = "a" * 20
        store.record(category="test", event_name="TEST_EVENT", data={"long": long_text})

        events = store.last(1)
        event = events[0]
        self.assertIsNotNone(event.data)
        self.assertEqual(len(event.data["long"]), 10)
        self.assertTrue(event.data["long"].endswith("..."))

    def test_eventrecord_to_dict_and_json(self):
        """Verify EventRecord.to_dict() and to_json() shapes and values."""
        store = EventStore()
        store.record(
            category="test",
            event_name="TYPE_X",
            agent="agent-1",
            severity="WARN",
            data={"k": "v"},
        )

        events = store.last(1)
        event = events[0]
        d = event.to_dict()

        # Basic keys
        self.assertEqual(d["seq"], event.seq)
        self.assertIn("timestamp", d)
        self.assertIsInstance(d["timestamp"], str)
        self.assertEqual(d["category"], "test")
        self.assertEqual(d["event_name"], "TYPE_X")
        self.assertEqual(d["agent"], "agent-1")
        data_dict = d["data"]
        self.assertIsInstance(data_dict, dict)
        self.assertEqual(data_dict["k"], "v")

        # JSON serialization returns a valid JSON string
        j = event.to_json()
        self.assertIsInstance(j, str)
        import json as _json

        parsed = _json.loads(j)
        self.assertEqual(parsed["seq"], event.seq)

    def test_ring_buffer_behavior(self):
        """Test ring buffer capacity limits."""
        store = EventStore(capacity=3)

        # Add 5 events
        for i in range(5):
            store.record(category="test", event_name=f"EVENT_{i}")

        # Should only keep last 3
        info = store.get_capacity_info()
        global_info = info["global"]
        self.assertIsInstance(global_info, dict)
        capacity_data = global_info["capacity"]
        self.assertIsInstance(capacity_data, dict)
        self.assertEqual(capacity_data["current_size"], 3)

        # Get all events in buffer
        events = store.last(100)  # Request more than exists
        self.assertEqual(len(events), 3)

        # Check we have events 3, 4, 5 (sequences continue counting)
        seqs = [e.seq for e in events]
        self.assertEqual(seqs, [3, 4, 5])

    def test_query_last_events(self):
        """Test querying last N events."""
        store = EventStore()

        # Add multiple events
        for i in range(10):
            store.record(
                category="test",
                event_name="TEST_EVENT",
                agent=f"agent-{i % 3}",
                data={"index": str(i)},
            )

        # Test basic last query
        events = store.last(5)
        self.assertEqual(len(events), 5)
        self.assertEqual([e.seq for e in events], [6, 7, 8, 9, 10])

    def test_query_filtered_by_agent(self):
        """Test filtering events by agent."""
        store = EventStore()

        # Add events for different agents
        for i in range(10):
            store.record(
                category="test", event_name="TEST_EVENT", agent=f"agent-{i % 3}"
            )

        # Filter by specific agent
        agent_events = store.last(agent="agent-1")
        self.assertGreater(len(agent_events), 0)
        self.assertTrue(all(e.agent == "agent-1" for e in agent_events))

    def test_query_filtered_by_type(self):
        """Test filtering events by type."""
        store = EventStore()

        # Add events of different types
        for i in range(10):
            store.record(category="test", event_name=f"TYPE_{i % 3}")

        # Filter by specific type
        type_events = store.last(event_name="TYPE_1")
        self.assertGreater(len(type_events), 0)
        self.assertTrue(all(e.event_name == "TYPE_1" for e in type_events))

    def test_query_after_sequence(self):
        """Test filtering events after sequence number."""
        store = EventStore()

        # Add 10 events
        for i in range(10):
            store.record(category="test", event_name="TEST_EVENT")

        # Get events after sequence 5
        events = store.last(after_seq=5)
        self.assertEqual(len(events), 5)
        self.assertTrue(all(e.seq > 5 for e in events))

    def test_stats_global(self):
        """Test global statistics."""
        store = EventStore()

        # Add events of different types
        for i in range(5):
            store.record(category="test", event_name="TYPE_A")
        for i in range(3):
            store.record(category="test", event_name="TYPE_B")

        stats = store.stats()
        self.assertEqual(stats["by_type"]["TYPE_A"], 5)
        self.assertEqual(stats["by_type"]["TYPE_B"], 3)

    def test_stats_by_agent(self):
        """Test statistics filtered by agent."""
        store = EventStore()

        # Add events for different agents and types
        for i in range(3):
            store.record(category="test", event_name="TYPE_A", agent="agent-1")
        for i in range(2):
            store.record(category="test", event_name="TYPE_B", agent="agent-1")
        for i in range(4):
            store.record(category="test", event_name="TYPE_A", agent="agent-2")

        # Check agent-1 stats
        agent1_stats = store.stats(agent="agent-1")
        self.assertEqual(agent1_stats["by_type"]["TYPE_A"], 3)
        self.assertEqual(agent1_stats["by_type"]["TYPE_B"], 2)

        # Check agent-2 stats
        agent2_stats = store.stats(agent="agent-2")
        self.assertEqual(agent2_stats["by_type"]["TYPE_A"], 4)
        self.assertNotIn("TYPE_B", agent2_stats["by_type"])

    def test_capacity_info(self):
        """Test capacity information."""
        store = EventStore(capacity=100)

        # Add some events
        for i in range(10):
            store.record(category="test", event_name="TEST_EVENT")

        info = store.get_capacity_info()
        global_info = info["global"]
        self.assertIsInstance(global_info, dict)
        capacity_data = global_info["capacity"]
        self.assertIsInstance(capacity_data, dict)
        self.assertEqual(capacity_data["capacity"], 100)
        self.assertEqual(capacity_data["current_size"], 10)
        self.assertEqual(capacity_data["oldest_seq"], 1)
        self.assertEqual(capacity_data["newest_seq"], 10)

    def test_thread_safety(self):
        """Test thread safety of EventStore."""
        store = EventStore()
        errors = []

        def worker(worker_id):
            try:
                for i in range(100):
                    store.record(
                        category="test",
                        event_name="CONCURRENT_EVENT",
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
        self.assertEqual(len(errors), 0)

        # Check capacity info shows 500 total events were recorded
        info = store.get_capacity_info()
        global_info = info["global"]
        self.assertIsInstance(global_info, dict)
        capacity_data = global_info["capacity"]
        self.assertIsInstance(capacity_data, dict)
        self.assertEqual(
            capacity_data["newest_seq"], 500
        )  # 5 workers * 100 events each

        # Check all events are properly recorded (default capacity is 5000, so all should be there)
        events = store.last(500)
        self.assertEqual(len(events), 500)


class TestOrchestratorEventIntegration(unittest.TestCase):
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

        self.assertTrue(hasattr(orchestrator, "event_store"))
        self.assertIsInstance(orchestrator.event_store, EventStore)

        # Verify capacity through public interface
        info = orchestrator.event_store.get_capacity_info()
        global_info = info["global"]
        self.assertIsInstance(global_info, dict)
        capacity_data = global_info["capacity"]
        self.assertIsInstance(capacity_data, dict)
        self.assertEqual(capacity_data["capacity"], 1000)

    def test_orchestrator_records_init_event(self):
        """Test that Orchestrator records initialization event."""
        orchestrator = Orchestrator(
            config=Orchestrator.Config(run_mode=RunMode.STOP_ON_EMPTY)
        )

        # Check that INIT event was recorded
        events = orchestrator.event_store.last()
        init_events = [e for e in events if e.event_name == "INIT"]
        self.assertEqual(len(init_events), 1)
        self.assertEqual(init_events[0].category, "orchestrator")
        self.assertIsNotNone(init_events[0].data)
        self.assertEqual(init_events[0].data["run_mode"], "stop_on_empty")

    def test_event_store_config_validation(self):
        """Test EventStore configuration validation."""
        # Test invalid history_max_events
        with self.assertRaises(Exception):  # Should raise validation error
            config = Orchestrator.Config(
                run_mode=RunMode.STOP_ON_EMPTY, history_max_events=0  # Invalid
            )
            config._validate()

        # Test invalid history_payload_bytes
        with self.assertRaises(Exception):  # Should raise validation error
            config = Orchestrator.Config(
                run_mode=RunMode.STOP_ON_EMPTY, history_payload_bytes=-1  # Invalid
            )
            config._validate()


if __name__ == "__main__":
    unittest.main()
