"""
Event Store for PyOrchestrate - Ring buffer based event history

This module provides efficient, lock-safe event storage with constant memory usage.
Uses a ring buffer (deque with maxlen) for O(1) append operations and minimal overhead.
"""

import time
import threading
from datetime import datetime
import json
from collections import deque, defaultdict
from typing import NamedTuple, Optional, List, Dict, Protocol, Iterable

from PyOrchestrate.core.utilities.event import OrchestratorEvent


class EventRecord(NamedTuple):
    """
    Immutable event record with minimal overhead.

    Attributes:
        seq: Sequential event number
        t_wall: Wall clock time (time.time())
        t_mono_ns: Monotonic time in nanoseconds for robust ordering
        category: Event category ("orchestrator" | "agent" | "cli")
        event_name: Event type (e.g., "AGENT_STARTED", "QUEUED", "CLI_COMMAND")
        agent: Agent name if applicable
        severity: Event severity ("INFO" | "WARN" | "ERROR")
        data: Optional payload data (truncated for efficiency)
    """

    seq: int
    t_wall: float
    t_mono_ns: int
    category: str
    event_name: str
    agent: Optional[str]
    severity: str
    data: Optional[dict[str, str]]

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serializable dict representation of the event.

        Includes an ISO8601 `timestamp` string for convenience while preserving
        numeric `t_wall` and `t_mono_ns` for consumers that need them.
        """
        data = dict(self.data) if self.data is not None else None
        return {
            "seq": self.seq,
            "t_wall": self.t_wall,
            "timestamp": datetime.fromtimestamp(self.t_wall).isoformat(),
            "t_mono_ns": self.t_mono_ns,
            "category": self.category,
            "event_name": self.event_name,
            "agent": self.agent,
            "severity": self.severity,
            "data": data,
        }

    def to_json(self, **json_kwargs) -> str:
        """Return a JSON string representation of the event.

        Passes json_kwargs to json.dumps (e.g. indent=2, ensure_ascii=False).
        """
        return json.dumps(self.to_dict(), **json_kwargs)


class StorePolicy(Protocol):
    """
    Protocol that defines the interface for event storage policies.

    Implementations can optimize storage strategies based on specific event types
    (e.g., keep only latest heartbeat per agent vs. full history for errors).
    """

    def append(self, e: "EventRecord") -> None:
        """Add a new event record to the store."""
        ...

    def last(
        self,
        n: int = 100,
        *,
        agent: Optional[str] = None,
        event_name: Optional[str] = None,
        after_seq: Optional[int] = None,
    ) -> List["EventRecord"]:
        """Retrieve the last N events with optional filtering.

        A non-positive `n` must return an empty list.
        """
        ...

    def stats(self, *, agent: Optional[str] = None) -> Dict[str, int]:
        """Get event count statistics, optionally for a specific agent.

        EventStore.stats() sums these counts across every configured store; an
        implementation that raises instead is skipped rather than failing the
        query.
        """
        ...

    def capacity_info(self) -> Dict[str, int]:
        """Get capacity and usage information for this store."""
        ...


class RingBufferStore(StorePolicy):
    """
    Fixed-capacity ring buffer store for event history.

    Features:
    - FIFO behavior: oldest events are automatically evicted when capacity is reached
    - O(1) append operations with constant memory usage
    - Maintains real-time event count statistics
    - Suitable for general event storage (errors, status changes, etc.)
    """

    def __init__(self, capacity: int):
        """
        Initialize the ring buffer store with a fixed capacity.

        Args:
            capacity (int): Maximum number of events to store.
        """
        self._buf: deque[EventRecord] = deque(maxlen=capacity)
        self._count_by_type: Dict[str, int] = defaultdict(int)
        self._count_by_agent_type: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

    def append(self, e: "EventRecord") -> None:
        """
        Add a new event to the ring buffer.

        If the buffer is at capacity, the oldest event is automatically removed.
        Updates internal statistics counters for fast stats() queries.

        Args:
            e: Event record to store
        """
        self._buf.append(e)
        self._count_by_type[e.event_name] += 1
        if e.agent:
            self._count_by_agent_type[e.agent][e.event_name] += 1

    def last(
        self,
        n: int = 100,
        *,
        agent: Optional[str] = None,
        event_name: Optional[str] = None,
        after_seq: Optional[int] = None,
    ) -> List["EventRecord"]:
        """
        Retrieve the most recent events from the ring buffer.

        Args:
            n: Maximum number of events to return. Non-positive values return
                an empty list.
            agent: Filter by specific agent name
            event_name: Filter by specific event type
            after_seq: Only return events with sequence number > after_seq

        Returns:
            List of EventRecord objects, most recent last
        """
        if n <= 0:
            return []
        items = list(self._buf)
        if after_seq is not None:
            items = [x for x in items if x.seq > after_seq]
        if agent is not None:
            items = [x for x in items if x.agent == agent]
        if event_name is not None:
            items = [x for x in items if x.event_name == event_name]
        return items[-n:]

    def stats(self, *, agent: Optional[str] = None) -> Dict[str, int]:
        """
        Get event count statistics with O(1) complexity.

        Counters track every appended event, so they keep growing after the
        buffer starts evicting: they answer "how many events were recorded",
        not "how many are still retained". Use capacity_info() for the
        retained size.

        Args:
            agent: If provided, return stats only for this agent

        Returns:
            Dictionary with event_name -> count mappings
        """
        if agent is None:
            return dict(self._count_by_type)
        return dict(self._count_by_agent_type.get(agent, {}))

    def capacity_info(self) -> Dict[str, int]:
        """
        Get current capacity and usage information for the ring buffer.

        Returns:
            Dictionary with capacity, current_size, oldest_seq, newest_seq
        """
        return {
            "capacity": self._buf.maxlen or 0,
            "current_size": len(self._buf),
            "oldest_seq": self._buf[0].seq if self._buf else 0,
            "newest_seq": self._buf[-1].seq if self._buf else 0,
        }


class BucketRingStore(StorePolicy):
    """
    Per-agent ring buffer store optimized for tracking latest events per agent.

    Features:
    - Separate ring buffer for each agent (bounded per-agent history)
    - Perfect for heartbeat monitoring: keeps only last N heartbeats per agent
    - O(1) append, efficient agent-specific queries
    - Events without agent are stored in a shared "_none" bucket
    - Memory usage scales with number of active agents
    """

    def __init__(self, per_agent_capacity: int):
        """
        Initialize the bucket ring store with a per-agent capacity.

        Args:
            per_agent_capacity: Maximum number of events to store per agent.
                               For heartbeat monitoring, typically use 1-3.
        """
        self._per_agent_capacity = per_agent_capacity
        self._buckets: Dict[str, deque[EventRecord]] = defaultdict(
            lambda: deque(maxlen=self._per_agent_capacity)
        )
        self._count_by_type: Dict[str, int] = defaultdict(int)
        self._count_by_agent_type: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

    def _bucket_key(self, agent: Optional[str]) -> str:
        """Convert agent name to bucket key, using '_none' for None agents."""
        return agent if agent is not None else "_none"

    def append(self, e: "EventRecord") -> None:
        """
        Add event to the appropriate agent bucket.

        Creates new buckets automatically for new agents.
        Oldest events are evicted when per-agent capacity is reached.

        Args:
            e: Event record to store
        """
        self._buckets[self._bucket_key(e.agent)].append(e)
        self._count_by_type[e.event_name] += 1
        if e.agent:
            self._count_by_agent_type[e.agent][e.event_name] += 1

    def last(
        self,
        n: int = 100,
        *,
        agent: Optional[str] = None,
        event_name: Optional[str] = None,
        after_seq: Optional[int] = None,
    ) -> List["EventRecord"]:
        """
        Retrieve recent events from per-agent buckets.

        Args:
            n: Maximum number of events to return. Non-positive values return
                an empty list.
            agent: If specified, only return events from this agent's bucket
            event_name: Filter by specific event type
            after_seq: Only return events with sequence number > after_seq

        Returns:
            List of EventRecord objects, sorted by sequence number (most recent last)
        """
        if n <= 0:
            return []
        if agent is not None:
            # Read through get(): _buckets is a defaultdict, and indexing it
            # here created a permanent bucket for every agent name asked
            # about. The name comes straight from the request -- `pyorchestrate
            # history --agent X --type agent_heartbeat`, or the same query over
            # HTTP -- so a store whose whole premise is constant memory grew
            # without bound, and capacity_info() reported those phantom agents
            # in `agents_known`. Only append() creates a bucket.
            items = list(self._buckets.get(self._bucket_key(agent), ()))
        else:
            # merge across all agents and take the most recent globally
            merged: List[EventRecord] = []
            for dq in self._buckets.values():
                merged.extend(dq)
            # sort by seq to keep global temporal order
            merged.sort(key=lambda e: e.seq)
            items = merged
        if after_seq is not None:
            items = [x for x in items if x.seq > after_seq]
        if event_name is not None:
            items = [x for x in items if x.event_name == event_name]
        return items[-n:]

    def stats(self, *, agent: Optional[str] = None) -> Dict[str, int]:
        """
        Get event count statistics with O(1) complexity.

        Counters track every appended event, so they keep growing after the
        per-agent buckets start evicting: they answer "how many events were
        recorded", not "how many are still retained". Use capacity_info() for
        the retained sizes.

        Args:
            agent: If provided, return stats only for this agent

        Returns:
            Dictionary with event_name -> count mappings
        """
        if agent is None:
            return dict(self._count_by_type)
        return dict(self._count_by_agent_type.get(agent, {}))

    def capacity_info(self) -> Dict[str, int]:
        """
        Get capacity and usage information for all agent buckets.

        Returns:
            Dictionary with per_agent_capacity, agents_known, approx_total_capacity,
            current_size, oldest_seq, newest_seq
        """
        total_current = sum(len(dq) for dq in self._buckets.values())
        # Report an approximate capacity based on known agents
        approx_capacity = len(self._buckets) * self._per_agent_capacity
        newest = max((dq[-1].seq for dq in self._buckets.values() if dq), default=0)
        oldest = min((dq[0].seq for dq in self._buckets.values() if dq), default=0)
        return {
            "per_agent_capacity": self._per_agent_capacity,
            "agents_known": len(self._buckets),
            "approx_total_capacity": approx_capacity,
            "current_size": total_current,
            "oldest_seq": oldest,
            "newest_seq": newest,
        }


class EventStore:
    """
    High-performance event storage with constant memory usage.

    Features:
    - Ring buffer with fixed capacity (no memory growth)
    - Thread-safe operations with minimal locking
    - Truncated payload to prevent memory bloat
    - Real-time aggregated counters for instant reports
    - Robust temporal ordering with monotonic timestamps
    - Pluggable storage policies per category (e.g., ring buffer vs. per-agent last-N)
    """

    def __init__(
        self,
        capacity: int = 5000,
        payload_max_bytes: int = 256,
        *,
        event_policies: Optional[Dict[str, StorePolicy]] = None,
    ):
        """
        Initialize the event store with default and custom storage policies.

        Args:
            capacity: Maximum number of events in the default ring buffer store
            payload_max_bytes: Maximum size for payload data strings (longer strings are truncated)
            event_policies: Optional mapping of event_name -> StorePolicy for event-specific storage.

        Example:
            ```python
            # Basic setup with default ring buffer
            store = EventStore()

            # Setup with heartbeat-optimized storage
            heartbeat_store = BucketRingStore(per_agent_capacity=1)
            store = EventStore(event_policies={"agent_heartbeat": heartbeat_store})
            ```
        """
        self._lock = threading.Lock()
        self._seq = 0
        self._payload_max = payload_max_bytes

        # Category-specific stores
        self._stores: Dict[str, StorePolicy] = {}
        """mapping {event_name -> StorePolicy}"""

        self._stores["__default__"] = RingBufferStore(capacity)
        if event_policies:
            self._stores.update(event_policies)

    def _truncate(self, s: str) -> str:
        """
        Truncate string to prevent memory bloat.

        Strings longer than payload_max_bytes are truncated with "..." suffix.
        """
        if s is None:
            return ""
        if len(s) <= self._payload_max:
            return s
        return s[: self._payload_max - 3] + "..."

    def record(
        self,
        *,
        category: str,
        event_name: str,
        agent: str | None = None,
        severity: str = "INFO",
        data: dict[str, str] | None = None,
    ) -> None:
        """
        Record a new event with O(1) complexity.

        Events are routed to appropriate storage policies based on event_name.
        If no specific policy exists for the event_name, uses the default ring buffer.

        Args:
            category: Event category ("orchestrator", "agent", "cli")
            event_name: Event type (e.g., "agent_heartbeat", "agent_error")
            agent: Agent name (optional, for agent-specific events)
            severity: Event severity level ("INFO", "WARN", "ERROR")
            data: Optional payload data (will be truncated if too long)

        Example:
            ```python
            store.record(
                category="agent",
                event_name="agent_heartbeat",
                agent="worker1",
                data={"timestamp": "2023-08-19T10:30:00"}
            )
            ```
        """
        tw = time.time()
        tm = time.monotonic_ns()

        # Truncate payload data to prevent memory issues
        if data:
            data = {k: self._truncate(str(v)) for k, v in data.items()}

        with self._lock:
            self._seq += 1
            rec = EventRecord(
                self._seq, tw, tm, category, event_name, agent, severity, data
            )

            # Route to category-specific policy store
            store = self._stores.get(event_name, self._stores["__default__"])
            store.append(rec)

    def last(
        self,
        n: int = 100,
        agent: str | None = None,
        event_name: str | None = None,
        after_seq: int | None = None,
    ) -> List[EventRecord]:
        """
        Retrieve recent events with optional filtering.

        Storage behavior:

        - If event_name is None: Merges results from all configured stores (default + any event-specific stores)
        - If event_name is specified: Uses the event-specific store if configured,
          otherwise falls back to the default ring buffer

        This design allows optimized storage per event type while maintaining
        backward compatibility for general queries.

        Args:
            n: Maximum number of events to return. Non-positive values return
                an empty list.
            agent: Filter by agent name (only events from this agent)
            event_name: Filter by event type (single event name only).
                       If None, searches in the default store containing all events.
            after_seq: Return only events after this sequence number

        Returns:
            List of EventRecord objects, ordered by sequence number (most recent last)

        Examples:
            ```python
            # Get last 50 events of any type (uses default ring buffer)
            all_events = store.last(50)

            # Get last 10 heartbeats (uses heartbeat-specific store if configured)
            heartbeats = store.last(10, event_name="agent_heartbeat")

            # Get last 20 events from specific agent (any event type)
            agent_events = store.last(20, agent="worker1")

            # Get heartbeats from specific agent
            agent_heartbeats = store.last(5, agent="worker1", event_name="agent_heartbeat")
            ```
        """
        if n <= 0:
            return []

        with self._lock:
            if event_name is None:
                merged: List[EventRecord] = []

                # Query default store (contains events that were routed to default)
                default_store = self._stores.get("__default__")
                if default_store is not None:
                    merged.extend(
                        default_store.last(
                            n=n, agent=agent, event_name=None, after_seq=after_seq
                        )
                    )

                # Query event-specific stores
                for name, store in self._stores.items():
                    if name == "__default__":
                        continue

                    try:
                        # Request up to `n` from each category store, filtering by agent/after_seq
                        merged.extend(
                            store.last(
                                n=n, agent=agent, event_name=name, after_seq=after_seq
                            )
                        )
                    except Exception:
                        # Be resilient: if a custom store behaves unexpectedly, skip it
                        continue

                # Merge by sequence number and return the last `n` events
                merged.sort(key=lambda e: e.seq)
                return merged[-n:]

            # Use event-specific store
            store = self._stores.get(event_name, self._stores["__default__"])
            return store.last(
                n=n, agent=agent, event_name=event_name, after_seq=after_seq
            )

    def latest(
        self, event_name: str, agent: Optional[str] = None
    ) -> Optional[EventRecord]:
        """
        Get the latest event of a specific type, optimized for O(1) access.

        Perfect for heartbeat monitoring and status checks.
        Uses the event-specific store if configured, providing efficient access
        to the most recent event without scanning through history.

        Args:
            event_name: Event type to look for (e.g., "agent_heartbeat")
            agent: Agent name. If None, gets latest across all agents

        Returns:
            Latest EventRecord or None if not found

        Example:
            ```python
            # Check if agent is alive (latest heartbeat)
            latest_hb = store.latest("agent_heartbeat", "worker1")
            if latest_hb and time.time() - latest_hb.t_wall < 30:
                print("Agent is alive")
            ```
        """
        with self._lock:
            store = self._stores.get(event_name, self._stores["__default__"])
            events = store.last(n=1, agent=agent, event_name=event_name)
            return events[0] if events else None

    def latest_all_agents(self, event_name: str) -> Dict[str, EventRecord]:
        """
        Get the latest event of a specific type for all agents.

        Extremely useful for heartbeat monitoring: get the last heartbeat
        from every agent in a single O(agents) operation.

        Optimized implementations:
        - BucketRingStore: Iterates through per-agent buckets efficiently
        - RingBufferStore: Scans events and groups by agent

        Args:
            event_name: Event type to look for (e.g., "agent_heartbeat")

        Returns:
            Dictionary mapping agent_name -> latest EventRecord
            (excludes agents with no events of this type)

        Example:
            ```python
            # Monitor all agent heartbeats
            heartbeats = store.latest_all_agents("agent_heartbeat")
            for agent, hb in heartbeats.items():
                age = time.time() - hb.t_wall
                if age > 30:
                    print(f"Agent {agent} missed heartbeat ({age:.1f}s ago)")
            ```
        """
        result: Dict[str, EventRecord] = {}
        with self._lock:
            store = self._stores.get(event_name, self._stores["__default__"])

            # For BucketRingStore, we can iterate through buckets efficiently
            if isinstance(store, BucketRingStore):
                for agent_key, bucket in store._buckets.items():
                    if agent_key == "_none":
                        continue
                    # Find latest event of this type in this agent's bucket
                    for event in reversed(bucket):
                        if event.event_name == event_name:
                            result[agent_key] = event
                            break
            else:
                # For RingBufferStore, get all events and group by agent
                events = store.last(n=10**9, event_name=event_name)
                agent_latest: Dict[str, EventRecord] = {}
                for event in events:
                    if event.agent:
                        agent_latest[event.agent] = event
                result = agent_latest

        return result

    def stats(self, agent: str | None = None) -> Dict[str, Dict[str, int]]:
        """
        Get aggregated event count statistics with O(1) complexity.

        Counts are summed across every configured store, so events routed to an
        event-specific policy are reported alongside the ones in the default
        ring buffer. A custom StorePolicy whose stats() raises is skipped rather
        than failing the whole query.

        The counters are cumulative since the store was created: they do not
        shrink when a buffer evicts its oldest events. Use get_capacity_info()
        for the number of events currently retained.

        Args:
            agent: Get stats for specific agent, or global stats if None

        Returns:
            Dictionary with "by_type" key containing event_name -> count mappings

        Example:
            ```python
            stats = store.stats()
            print(f"Total heartbeats: {stats['by_type'].get('agent_heartbeat', 0)}")
            ```
        """
        with self._lock:
            by_type: Dict[str, int] = defaultdict(int)
            for store in self._stores.values():
                try:
                    counts = store.stats(agent=agent)
                except Exception:
                    # Be resilient: a custom store may not collect statistics
                    continue
                for event_name, count in counts.items():
                    by_type[event_name] += count
            return {"by_type": dict(by_type)}

    def get_capacity_info(self) -> Dict[str, Dict[str, Dict[str, int]]]:
        """
        Get current capacity and usage information for all storage policies.

        Returns:
            Dictionary with:
            - "stores": Dictionary mapping store_name -> capacity_info for ALL stores
              - "__default__": The default RingBufferStore capacity info
              - event-specific stores (e.g., "agent_heartbeat"): Custom store capacity info
            - "summary": High-level aggregated information
              - "total_stores": Total number of configured stores
              - "total_events_approx": Approximate total events across all stores

        Useful for monitoring memory usage and detecting storage issues.

        Example:
            ```python
            info = store.get_capacity_info()
            default_info = info['stores']['__default__']
            hb_info = info['stores'].get('agent_heartbeat', {})
            total_stores = info['summary']['total_stores']
            ```
        """
        with self._lock:
            stores_info = {}
            total_events = 0

            # Collect capacity info from all stores (including default)
            for store_name, store in self._stores.items():
                capacity_info = store.capacity_info()
                stores_info[store_name] = capacity_info

                # Accumulate total events (current_size if available)
                if "current_size" in capacity_info:
                    total_events += capacity_info["current_size"]

            info = {
                "stores": stores_info,
                "summary": {
                    "total_stores": len(self._stores),
                    "total_events_approx": total_events,
                },
            }
        return info
