---
title: OrchestratorEventBus
editLink: true
---

# OrchestratorEventBus

The **OrchestratorEventBus** is a unified facade that combines event management and history tracking into a single, cohesive interface. It serves as the central nervous system for all orchestrator events, bridging real-time event handling with historical data storage.

## Purpose and Design

Before the refactoring, the Orchestrator managed `EventManager` and `EventStore` separately, requiring developers to interact with both components independently. The `OrchestratorEventBus` unifies these components, providing:

- **Single Point of Access**: One interface for all event-related operations
- **Automatic History Recording**: Events are automatically stored when emitted
- **Simplified API**: Developers work with one component instead of two
- **Event Policies**: Configurable retention rules for different event types

## Core Responsibilities

| Responsibility | Description |
|---------------|-------------|
| **Callback Management** | Register and execute callbacks for orchestrator events |
| **Event Emission** | Emit events and notify all registered callbacks |
| **History Tracking** | Automatically record all emitted events to history |
| **Query Interface** | Search and retrieve historical events |
| **Policy Enforcement** | Apply custom retention policies per event type |

## How It Works

The EventBus acts as a coordinator between two internal components:

```
User Code
    ↓
OrchestratorEventBus
    ├─→ EventManager (handles callbacks)
    └─→ EventStore (records history)
```

When you emit an event through the EventBus:
1. **EventManager** executes all registered callbacks immediately
2. **EventStore** records the event to history automatically
3. Both operations happen transparently in a single call

## Basic Usage

### Registering Event Callbacks

Subscribe to orchestrator events to react to system changes:

```python
from PyOrchestrate.core.utilities.event import OrchestratorEvent

def on_agent_started(agent_name, event_date, event_time, **kwargs):
    print(f"Agent '{agent_name}' started at {event_time}")

# Register callback
orchestrator.event_bus.register_callback(
    OrchestratorEvent.AGENT_STARTED,
    on_agent_started
)
```

### Emitting Events

Emit events to notify all subscribers and record to history:

```python
# Emit event (automatically recorded to history)
orchestrator.event_bus.emit(
    OrchestratorEvent.AGENT_STARTED,
    agent_name="worker1",
    event_date="2025-10-26",
    event_time="14:30:00"
)
```

### Querying Event History

Retrieve historical events for analysis or debugging:

```python
# Get all agent-related events
recent_events = orchestrator.event_bus.event_store.query(
    category="agent",
    limit=50
)

# Get specific event type
started_events = orchestrator.event_bus.event_store.query(
    event_name="AGENT_STARTED",
    limit=10
)
```

## Event Types

The EventBus handles all `OrchestratorEvent` types:

| Event | Triggered When | Key Data |
|-------|---------------|----------|
| `AGENT_STARTED` | Agent begins execution | `agent_name`, `event_date`, `event_time` |
| `AGENT_READY` | Agent signals readiness | `agent_name`, `event_date`, `event_time` |
| `AGENT_TERMINATED` | Agent completes or stops | `agent_name`, `event_date`, `event_time` |
| `AGENT_ERROR` | Agent encounters error | `agent_name`, `error_message`, timestamps |
| `AGENT_HEARTBEAT` | Agent sends periodic heartbeat | `agent_name`, timestamps |

## Event History and Storage

### Ring Buffer Architecture

The EventStore uses a **ring buffer** to maintain a fixed-capacity event history:

```python
config = OrchestratorConfig(
    history_max_events=1000  # Keep last 1000 events
)
```

When the buffer fills up, the oldest events are automatically discarded to make room for new ones.

### Event Capacity Configuration

Control how much history to retain:

```python
# Minimal history (conserve memory)
config = OrchestratorConfig(
    history_max_events=100,
    history_payload_bytes=1000
)

# Extensive history (debugging/analysis)
config = OrchestratorConfig(
    history_max_events=10000,
    history_payload_bytes=50000
)
```

## Event Policies

Event policies allow you to define **custom retention rules** for specific event types. This is particularly useful for high-frequency events like heartbeats.

### Built-in Policy: BucketRingStore

The `BucketRingStore` policy keeps only the last N events of a specific type:

```python
from PyOrchestrate.core.orchestrator import EventStore, BucketRingStore

# Keep only the last 2 heartbeats per agent
event_store = EventStore(
    capacity=1000,
    event_policies={
        "AGENT_HEARTBEAT": BucketRingStore(capacity=2)
    }
)

orchestrator = Orchestrator()
orchestrator.event_bus = OrchestratorEventBus(event_store)
```

**Benefits**:
- Prevents heartbeat events from flooding the event history
- Maintains recent heartbeat data for liveness checks
- Frees space for more important events

### Custom Event Policies

You can implement custom policies by creating classes that follow the policy interface:

```python
class CustomPolicy:
    def should_store(self, event_name: str, event_data: dict) -> bool:
        """Decide whether to store this event"""
        # Example: Only store errors from specific agents
        if event_name == "AGENT_ERROR":
            return event_data.get("agent_name") in ["critical_agent_1", "critical_agent_2"]
        return True
    
    def get_capacity(self) -> int:
        """Return max events to store"""
        return 100
```

## Thread Safety

The OrchestratorEventBus is **thread-safe** and can be safely accessed from multiple threads:

- Callbacks are executed in a thread pool (non-blocking)
- Event storage uses locks to prevent race conditions
- Multiple agents can emit events concurrently without conflicts

## Integration with MessageRouter

The EventBus receives events from the `MessageRouter`, which translates agent messages into orchestrator events:

```
Agent sends message
    ↓
MessageRouter receives and translates
    ↓
OrchestratorEventBus.emit()
    ├─→ Execute callbacks
    └─→ Record to history
```

This automatic integration means you don't need to manually emit agent lifecycle events—they're handled by the framework.

## Common Patterns

### Monitoring Agent Health

```python
def check_agent_health(agent_name, **kwargs):
    """Monitor agent status"""
    last_heartbeat = orchestrator.event_bus.event_store.query(
        event_name="AGENT_HEARTBEAT",
        limit=1
    )
    
    if not last_heartbeat:
        logger.warning(f"No heartbeat received from {agent_name}")

orchestrator.event_bus.register_callback(
    OrchestratorEvent.AGENT_HEARTBEAT,
    check_agent_health
)
```

### Logging All Agent Errors

```python
def log_error(agent_name, error_message, **kwargs):
    """Log all agent errors to external system"""
    external_logger.error(f"Agent {agent_name}: {error_message}")

orchestrator.event_bus.register_callback(
    OrchestratorEvent.AGENT_ERROR,
    log_error
)
```

### Analytics and Reporting

```python
def generate_report():
    """Generate agent execution report"""
    events = orchestrator.event_bus.event_store.query(
        category="agent",
        limit=1000
    )
    
    started = len([e for e in events if e.event_name == "AGENT_STARTED"])
    completed = len([e for e in events if e.event_name == "AGENT_TERMINATED"])
    errors = len([e for e in events if e.event_name == "AGENT_ERROR"])
    
    print(f"Report: {started} started, {completed} completed, {errors} errors")
```

## Comparison: Before vs After Refactoring

### Before (Separate Components)

```python
# Register callback
orchestrator.event_manager.register_callback(event, callback)

# Emit event
orchestrator.event_manager.emit(event, **data)

# Query history (separate component!)
orchestrator.event_store.query(category="agent")
```

### After (Unified EventBus)

```python
# Register callback
orchestrator.event_bus.register_callback(event, callback)

# Emit event (automatically recorded)
orchestrator.event_bus.emit(event, **data)

# Query history (same component!)
orchestrator.event_bus.event_store.query(category="agent")
```

The unified interface reduces cognitive load and ensures events are always recorded to history.

## Best Practices

### 1. Use Specific Event Types

```python
# Good: Specific event subscription
orchestrator.event_bus.register_callback(
    OrchestratorEvent.AGENT_ERROR,
    handle_errors
)

# Avoid: Catching all events (performance impact)
for event_type in OrchestratorEvent:
    orchestrator.event_bus.register_callback(event_type, handle_all)
```

### 2. Keep Callbacks Lightweight

```python
# Good: Quick callback that delegates heavy work
def on_agent_error(agent_name, error_message, **kwargs):
    task_queue.put((agent_name, error_message))  # Fast enqueue

# Avoid: Heavy processing in callback (blocks thread pool)
def on_agent_error(agent_name, error_message, **kwargs):
    send_email_alert(...)  # Slow operation
    update_database(...)   # Blocks other callbacks
```

### 3. Configure Appropriate History Size

```python
# Development: Small history
config = OrchestratorConfig(history_max_events=100)

# Production: Larger history for debugging
config = OrchestratorConfig(history_max_events=5000)
```

### 4. Use Event Policies for High-Frequency Events

```python
# Without policy: Heartbeats flood the history
# With policy: Only keep last 2 heartbeats
event_policies = {
    "AGENT_HEARTBEAT": BucketRingStore(capacity=2)
}
```

## See Also

- [MessageRouter](./message-router.md) - Routes agent messages to EventBus
- [EventManager](../utilities/event-manager.md) - Low-level callback system
- [Orchestrator Internals](./index.md) - Architecture overview
