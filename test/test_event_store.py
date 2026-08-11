"""
Test cases for Event History functionality

Tests the EventStore class and integration with Orchestrator.
"""

import unittest
import threading

from PyOrchestrate.core.orchestrator.event_store import (
    BucketRingStore,
    EventRecord,
    EventStore,
    RingBufferStore,
)
from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator, RunMode


class TestEventStore(unittest.TestCase):
    """Test the EventStore class functionality."""

    def test_event_store_initialization(self):
        """Test EventStore initializes with correct defaults."""
        store = EventStore()
        # Test using public interface
        info = store.get_capacity_info()
        default_store_info = info["stores"]["__default__"]
        self.assertIsInstance(default_store_info, dict)
        self.assertEqual(default_store_info["capacity"], 5000)
        self.assertEqual(info["summary"]["total_stores"], 1)
        self.assertEqual(len(store.last(1)), 0)  # No events recorded yet

    def test_event_store_custom_capacity(self):
        """Test EventStore with custom capacity."""
        store = EventStore(capacity=100, payload_max_bytes=64)
        info = store.get_capacity_info()
        default_store_info = info["stores"]["__default__"]
        self.assertIsInstance(default_store_info, dict)
        self.assertEqual(default_store_info["capacity"], 100)

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
        default_store_info = info["stores"]["__default__"]
        self.assertIsInstance(default_store_info, dict)
        self.assertEqual(default_store_info["current_size"], 3)

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

    def test_last_with_non_positive_n_returns_nothing(self):
        """A request for zero or fewer events must not return the whole buffer."""
        store = EventStore()

        for _ in range(10):
            store.record(category="test", event_name="TYPE_A", agent="agent-1")

        # Merged path (no event_name filter)
        self.assertEqual(store.last(n=0), [])
        self.assertEqual(store.last(n=-3), [])
        # Filtered paths
        self.assertEqual(store.last(n=0, event_name="TYPE_A"), [])
        self.assertEqual(store.last(n=0, agent="agent-1"), [])
        # A positive request is unaffected
        self.assertEqual(len(store.last(n=4)), 4)

    def test_last_with_non_positive_n_returns_nothing_for_policy_store(self):
        """The clamp also applies to events routed to an event-specific store."""
        store = EventStore(event_policies={"agent_heartbeat": BucketRingStore(2)})

        for _ in range(6):
            store.record(category="agent", event_name="agent_heartbeat", agent="w1")

        self.assertEqual(store.last(n=0, event_name="agent_heartbeat"), [])
        self.assertEqual(store.last(n=-1, event_name="agent_heartbeat"), [])
        self.assertEqual(store.last(n=0), [])
        self.assertEqual(len(store.last(n=1, event_name="agent_heartbeat")), 1)

    def test_stats_include_event_specific_stores(self):
        """Events routed to a policy store are counted, not silently dropped."""
        store = EventStore(event_policies={"agent_heartbeat": BucketRingStore(2)})

        for _ in range(4):
            store.record(category="orchestrator", event_name="agent_started")
        for _ in range(6):
            store.record(category="agent", event_name="agent_heartbeat", agent="w1")

        by_type = store.stats()["by_type"]
        self.assertEqual(by_type["agent_started"], 4)
        self.assertEqual(by_type["agent_heartbeat"], 6)

    def test_stats_by_agent_include_event_specific_stores(self):
        """The agent filter reaches the policy stores too."""
        store = EventStore(event_policies={"agent_heartbeat": BucketRingStore(2)})

        for _ in range(3):
            store.record(category="agent", event_name="agent_heartbeat", agent="w1")
        for _ in range(5):
            store.record(category="agent", event_name="agent_heartbeat", agent="w2")
        store.record(category="orchestrator", event_name="agent_started", agent="w1")

        w1_stats = store.stats(agent="w1")["by_type"]
        self.assertEqual(w1_stats["agent_heartbeat"], 3)
        self.assertEqual(w1_stats["agent_started"], 1)

        w2_stats = store.stats(agent="w2")["by_type"]
        self.assertEqual(w2_stats["agent_heartbeat"], 5)
        self.assertNotIn("agent_started", w2_stats)

    def test_stats_skip_a_policy_that_does_not_collect_them(self):
        """A custom policy whose stats() raises must not fail the whole query."""

        class NoStatsStore(RingBufferStore):
            def stats(self, *, agent=None):
                raise NotImplementedError

        store = EventStore(event_policies={"custom": NoStatsStore(10)})

        store.record(category="test", event_name="custom")
        for _ in range(2):
            store.record(category="test", event_name="TYPE_A")

        by_type = store.stats()["by_type"]
        self.assertEqual(by_type["TYPE_A"], 2)
        self.assertNotIn("custom", by_type)

    def test_capacity_info(self):
        """Test capacity information."""
        store = EventStore(capacity=100)

        # Add some events
        for i in range(10):
            store.record(category="test", event_name="TEST_EVENT")

        info = store.get_capacity_info()
        default_store_info = info["stores"]["__default__"]
        self.assertIsInstance(default_store_info, dict)
        self.assertEqual(default_store_info["capacity"], 100)
        self.assertEqual(default_store_info["current_size"], 10)
        self.assertEqual(default_store_info["oldest_seq"], 1)
        self.assertEqual(default_store_info["newest_seq"], 10)

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
        default_store_info = info["stores"]["__default__"]
        self.assertIsInstance(default_store_info, dict)
        self.assertEqual(
            default_store_info["newest_seq"], 500
        )  # 5 workers * 100 events each

        # Check all events are properly recorded (default capacity is 5000, so all should be there)
        events = store.last(500)
        self.assertEqual(len(events), 500)


class TestStorePolicies(unittest.TestCase):
    """Test the built-in StorePolicy implementations directly."""

    @staticmethod
    def _record(seq: int, event_name: str = "TYPE_A", agent: str = "w1") -> EventRecord:
        return EventRecord(
            seq=seq,
            t_wall=0.0,
            t_mono_ns=seq,
            category="test",
            event_name=event_name,
            agent=agent,
            severity="INFO",
            data=None,
        )

    def test_ring_buffer_store_last_with_non_positive_n(self):
        """RingBufferStore returns nothing when asked for zero or fewer events."""
        store = RingBufferStore(capacity=10)
        for seq in range(1, 6):
            store.append(self._record(seq))

        self.assertEqual(store.last(n=0), [])
        self.assertEqual(store.last(n=-2), [])
        self.assertEqual(len(store.last(n=3)), 3)

    def test_bucket_ring_store_last_with_non_positive_n(self):
        """BucketRingStore returns nothing when asked for zero or fewer events."""
        store = BucketRingStore(per_agent_capacity=3)
        for seq in range(1, 6):
            store.append(self._record(seq))

        self.assertEqual(store.last(n=0), [])
        self.assertEqual(store.last(n=-2), [])
        self.assertEqual(store.last(n=0, agent="w1"), [])
        self.assertEqual(len(store.last(n=2)), 2)

    def test_bucket_ring_store_stats_count_recorded_not_retained(self):
        """Counters keep rising once the per-agent buckets start evicting."""
        store = BucketRingStore(per_agent_capacity=2)
        for seq in range(1, 8):
            store.append(self._record(seq))

        # Only 2 events survive in the bucket, but all 7 were recorded.
        self.assertEqual(store.capacity_info()["current_size"], 2)
        self.assertEqual(store.stats()["TYPE_A"], 7)
        self.assertEqual(store.stats(agent="w1")["TYPE_A"], 7)

    def test_bucket_ring_store_stats_are_per_agent(self):
        """Each agent gets its own counters."""
        store = BucketRingStore(per_agent_capacity=2)
        store.append(self._record(1, agent="w1"))
        store.append(self._record(2, agent="w1"))
        store.append(self._record(3, agent="w2", event_name="TYPE_B"))

        self.assertEqual(store.stats(), {"TYPE_A": 2, "TYPE_B": 1})
        self.assertEqual(store.stats(agent="w1"), {"TYPE_A": 2})
        self.assertEqual(store.stats(agent="w2"), {"TYPE_B": 1})
        self.assertEqual(store.stats(agent="unknown"), {})

    def test_bucket_ring_store_query_does_not_create_a_bucket(self):
        """Reading the history of an unknown agent must not allocate for it."""
        store = BucketRingStore(per_agent_capacity=2)
        store.append(self._record(1, agent="w1"))

        for index in range(50):
            self.assertEqual(store.last(n=5, agent=f"ghost-{index}"), [])

        self.assertEqual(store.capacity_info()["agents_known"], 1)

    def test_event_store_query_does_not_create_a_bucket(self):
        """The same, through the query path the CLI and the web API use."""
        store = EventStore(
            capacity=10,
            event_policies={"agent_heartbeat": BucketRingStore(per_agent_capacity=2)},
        )
        store.record(category="agent", event_name="agent_heartbeat", agent="w1")

        for index in range(50):
            store.last(n=5, agent=f"ghost-{index}", event_name="agent_heartbeat")
            store.latest("agent_heartbeat", agent=f"ghost-{index}")

        heartbeats = store.get_capacity_info()["stores"]["agent_heartbeat"]
        self.assertEqual(heartbeats["agents_known"], 1)


class TestOrchestratorEventIntegration(unittest.TestCase):
    """Test EventStore integration with Orchestrator."""

    def test_orchestrator_has_event_store(self):
        """Test that Orchestrator initializes with EventStore."""
        orchestrator = Orchestrator(
            config=Orchestrator.Config(
                run_mode=RunMode.STOP_ON_EMPTY,
                enable_command_interface=False,
                history_max_events=1000,
                history_payload_bytes=512,
            )
        )

        self.assertTrue(hasattr(orchestrator, "event_bus"))
        self.assertIsInstance(orchestrator.event_bus.event_store, EventStore)

        # Verify capacity through public interface
        info = orchestrator.event_bus.event_store.get_capacity_info()
        default_store_info = info["stores"]["__default__"]
        self.assertIsInstance(default_store_info, dict)
        self.assertEqual(default_store_info["capacity"], 1000)

    def test_orchestrator_records_init_event(self):
        """Test that Orchestrator records initialization event."""
        orchestrator = Orchestrator(
            config=Orchestrator.Config(
                run_mode=RunMode.STOP_ON_EMPTY, enable_command_interface=False
            )
        )

        # Check that INIT event was recorded
        events = orchestrator.event_bus.event_store.last()
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
