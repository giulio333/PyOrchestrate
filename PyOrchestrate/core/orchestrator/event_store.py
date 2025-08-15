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
from typing import NamedTuple, Optional, List, Dict


class EventRecord(NamedTuple):
    """
    Immutable event record with minimal overhead.

    Attributes:
        seq: Sequential event number
        t_wall: Wall clock time (time.time())
        t_mono_ns: Monotonic time in nanoseconds for robust ordering
        category: Event category ("orchestrator" | "agent" | "cli")
        type: Event type (e.g., "AGENT_STARTED", "QUEUED", "CLI_COMMAND")
        agent: Agent name if applicable
        severity: Event severity ("INFO" | "WARN" | "ERROR")
        data: Optional payload data (truncated for efficiency)
    """

    seq: int
    t_wall: float
    t_mono_ns: int
    category: str
    type: str
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
            "type": self.type,
            "agent": self.agent,
            "severity": self.severity,
            "data": data,
        }

    def to_json(self, **json_kwargs) -> str:
        """Return a JSON string representation of the event.

        Passes json_kwargs to json.dumps (e.g. indent=2, ensure_ascii=False).
        """
        return json.dumps(self.to_dict(), **json_kwargs)


class EventStore:
    """
    High-performance event storage with constant memory usage.

    Features:
    - Ring buffer with fixed capacity (no memory growth)
    - Thread-safe operations with minimal locking
    - Truncated payload to prevent memory bloat
    - Real-time aggregated counters for instant reports
    - Robust temporal ordering with monotonic timestamps
    """

    def __init__(self, capacity: int = 5000, payload_max_bytes: int = 256):
        """
        Initialize the event store.

        Args:
            capacity: Maximum number of events to store (ring buffer size)
            payload_max_bytes: Maximum size for payload data strings
        """
        self._events = deque(maxlen=capacity)
        self._lock = threading.Lock()
        self._seq = 0
        self._payload_max = payload_max_bytes

        # Aggregated counters for instant statistics
        self._count_by_type = defaultdict(int)
        self._count_by_agent_type = defaultdict(lambda: defaultdict(int))

    def _truncate(self, s: str) -> str:
        """Truncate string to prevent memory bloat."""
        if s is None:
            return ""
        if len(s) <= self._payload_max:
            return s
        return s[: self._payload_max - 3] + "..."

    def record(
        self,
        *,
        category: str,
        type: str,
        agent: str | None = None,
        severity: str = "INFO",
        data: dict[str, str] | None = None,
    ) -> None:
        """
        Record a new event with O(1) complexity.

        Args:
            category: Event category ("orchestrator", "agent", "cli")
            type: Event type identifier
            agent: Agent name (optional)
            severity: Event severity level
            data: Optional payload data (will be truncated)
        """
        tw = time.time()
        tm = time.monotonic_ns()

        # Truncate payload data to prevent memory issues
        if data:
            data = {k: self._truncate(str(v)) for k, v in data.items()}

        with self._lock:
            self._seq += 1
            rec = EventRecord(self._seq, tw, tm, category, type, agent, severity, data)
            self._events.append(rec)

            # Update aggregated counters
            self._count_by_type[type] += 1
            if agent:
                self._count_by_agent_type[agent][type] += 1

    def last(
        self,
        n: int = 100,
        agent: str | None = None,
        type: str | None = None,
        after_seq: int | None = None,
    ) -> List[EventRecord]:
        """
        Retrieve recent events with optional filtering.

        Args:
            n: Maximum number of events to return
            agent: Filter by agent name
            type: Filter by event type
            after_seq: Return only events after this sequence number

        Returns:
            List of EventRecord objects matching the criteria
        """
        with self._lock:
            # Create a snapshot of current events
            events_snapshot = list(self._events)

        # Apply filters
        if after_seq is not None:
            events_snapshot = [e for e in events_snapshot if e.seq > after_seq]
        if agent is not None:
            events_snapshot = [e for e in events_snapshot if e.agent == agent]
        if type is not None:
            events_snapshot = [e for e in events_snapshot if e.type == type]

        # Return last n events
        return events_snapshot[-n:]

    def stats(self, agent: str | None = None) -> Dict[str, Dict[str, int]]:
        """
        Get aggregated statistics with O(1) complexity.

        Args:
            agent: Get stats for specific agent, or global if None

        Returns:
            Dictionary with event type counts
        """
        with self._lock:
            if agent is None:
                return {"by_type": dict(self._count_by_type)}
            return {"by_type": dict(self._count_by_agent_type.get(agent, {}))}

    def get_capacity_info(self) -> Dict[str, int]:
        """
        Get current capacity and usage information.

        Returns:
            Dictionary with capacity stats
        """
        with self._lock:
            return {
                "capacity": self._events.maxlen or 0,
                "current_size": len(self._events),
                "total_events": self._seq,
                "oldest_seq": self._events[0].seq if self._events else 0,
                "newest_seq": self._events[-1].seq if self._events else 0,
            }
