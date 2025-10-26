---
title: MessageRouter
editLink: true
---

# MessageRouter

The **MessageRouter** is responsible for routing messages from agents to the orchestrator's event system. It acts as a translation layer that converts agent-specific messages into orchestrator events.

## Purpose and Design

Agents and the orchestrator run in separate processes (or threads) and need a way to communicate. Agents send status updates, error notifications, and heartbeats to the orchestrator, which must be translated into orchestrator events that trigger registered callbacks and get recorded in event history.

The MessageRouter bridges this gap by:
- Listening for messages from agents via the `MessageChannel`
- Translating `AgentEvent` types to `OrchestratorEvent` types
- Filtering out messages from terminated agents
- Managing its own lifecycle independently

## Core Responsibilities

| Responsibility | Description |
|---------------|-------------|
| **Message Reception** | Listen for incoming agent messages via MessageChannel |
| **Event Translation** | Convert agent events to orchestrator events |
| **Message Filtering** | Ignore messages from terminated agents |
| **Lifecycle Management** | Start/stop background message handling thread |
| **Error Handling** | Handle malformed messages and connection issues |

## Communication Flow

```
Agent (separate process)
    ↓ sends ServiceMessage
MessageChannel (process-safe queue)
    ↓ receives message
MessageRouter (background thread)
    ↓ translates to OrchestratorEvent
OrchestratorEventBus
    ├─→ Execute callbacks
    └─→ Record to history
```

## How It Works

### Background Thread Operation

The MessageRouter runs in a **background thread** that continuously polls the MessageChannel for incoming messages:

1. Agent sends a `ServiceMessage` (e.g., "I'm ready")
2. MessageRouter receives the message via `ChannelHandler`
3. Router translates `AgentEvent.AGENT_READY` → `OrchestratorEvent.AGENT_READY`
4. Router calls `event_bus.emit(OrchestratorEvent.AGENT_READY, ...)`
5. Callbacks are executed and event is recorded to history

### Event Type Mapping

The router maintains an internal mapping between agent and orchestrator events:

| AgentEvent | OrchestratorEvent | Purpose |
|-----------|-------------------|---------|
| `AGENT_STARTED` | `AGENT_STARTED` | Agent has started execution |
| `AGENT_READY` | `AGENT_READY` | Agent is ready to work |
| `AGENT_TERMINATED` | `AGENT_TERMINATED` | Agent has stopped |
| `AGENT_ERROR` | `AGENT_ERROR` | Agent encountered an error |
| `AGENT_HEARTBEAT` | `AGENT_HEARTBEAT` | Agent is alive |

## Lifecycle Management

### Starting the Router

The MessageRouter is started automatically when the Orchestrator initializes:

```python
# In Orchestrator.__init__()
self.message_router = MessageRouter(
    message_channel=self.message_channel,
    event_bus=self.event_bus,
    logger=self.logger
)

# Automatically started
self.message_router.start()
```

### Stopping the Router

The router is stopped during orchestrator shutdown:

```python
# During Orchestrator.join() cleanup
self.message_router.stop(timeout=2.0)
```

The `stop()` method:
- Signals the background thread to exit
- Waits up to `timeout` seconds for graceful shutdown
- Ensures all pending messages are processed

## Message Filtering

### Terminated Agent Filtering

The MessageRouter maintains a set of terminated agents and filters out their messages:

```python
# When agent terminates
message_router.mark_agent_terminated("worker1")

# Future messages from worker1 are ignored
# Prevents stale messages from affecting the orchestrator
```

**Why filtering is important**:
- Agents may send messages during shutdown
- Message queue may contain delayed messages
- Prevents confusion with agents that have the same name but different instances

### Filter Behavior

```
Agent "worker1" terminates → mark_agent_terminated("worker1")
    ↓
Message arrives from "worker1"
    ↓
Router checks: is "worker1" in terminated set?
    ↓ YES
Message is ignored (not converted to event)
```

## Integration with MessageChannel

The MessageRouter uses the `MessageChannel` for inter-process communication:

### Process-Safe Communication

```
Agent Process A          MessageChannel          Orchestrator Process
    |                         |                         |
    |--ServiceMessage-------->|                         |
    |                         |<----poll message--------|
    |                         |                         |
    |                         |----message------------->|
    |                         |                    MessageRouter
```

### Message Format

Agents send structured `ServiceMessage` objects:

```python
# Agent sends ready notification
self.send_message(ServiceMessage.create_status(
    sender=self.name,
    status="ready",
    event_name=AgentEvent.AGENT_READY.value
))
```

The MessageRouter receives and extracts:
- `sender`: Agent name
- `event_name`: Type of event
- Additional data (error messages, timestamps, etc.)

## Error Handling

### Malformed Messages

```python
# If message is missing required fields
try:
    event_name = message.get("event_name")
    sender = message.get("sender")
except KeyError as e:
    logger.error(f"Malformed message: {e}")
    # Message is discarded, router continues
```

### Connection Issues

```python
# If MessageChannel connection fails
try:
    message = channel_handler.receive()
except ChannelError as e:
    logger.error(f"Channel error: {e}")
    # Retry logic or graceful degradation
```

### Event Emission Failures

```python
# If event_bus.emit() raises exception
try:
    event_bus.emit(event_type, **event_data)
except Exception as e:
    logger.error(f"Failed to emit event: {e}")
    # Error is logged but router continues processing
```

## Common Patterns

### Monitoring Message Flow

```python
# Log all messages being routed
def on_message_routed(event_type, **kwargs):
    logger.debug(f"Routed: {event_type} with data {kwargs}")

orchestrator.event_bus.register_callback(
    OrchestratorEvent.AGENT_READY,
    on_message_routed
)
```

### Detecting Communication Issues

```python
# Check if agents are sending messages
last_message_time = time.time()

def update_last_message(**kwargs):
    global last_message_time
    last_message_time = time.time()

orchestrator.event_bus.register_callback(
    OrchestratorEvent.AGENT_HEARTBEAT,
    update_last_message
)

# Alert if no messages received for too long
if time.time() - last_message_time > 60:
    logger.error("No agent messages received in 60 seconds!")
```

## Performance Considerations

### Non-Blocking Design

The MessageRouter runs in a **separate thread**, ensuring:
- Message routing never blocks the main orchestrator loop
- Multiple agents can send messages concurrently
- Slow event callbacks don't delay message processing

### Message Queue Depth

The underlying MessageChannel maintains a queue of messages:
- Large queue = can buffer many messages (uses more memory)
- Small queue = may lose messages under high load
- Default settings work for most use cases

### Filtering Overhead

Checking if an agent is terminated is **O(1)** (set lookup):
```python
# Very fast operation
if sender in self._terminated_agents:
    return  # Skip message
```

## Comparison with Direct Event Emission

### Without MessageRouter (before refactoring)

```python
# Orchestrator had to manually check messages
while True:
    msg = message_channel.receive()
    if msg.event_name == "AGENT_READY":
        event_manager.emit(OrchestratorEvent.AGENT_READY, ...)
    elif msg.event_name == "AGENT_ERROR":
        event_manager.emit(OrchestratorEvent.AGENT_ERROR, ...)
    # ... more conditions
```

### With MessageRouter (after refactoring)

```python
# MessageRouter handles everything automatically
message_router.start()  # That's it!
```

The refactored design eliminates boilerplate and centralizes message routing logic.

## Best Practices

### 1. Let the Framework Handle It

```python
# Good: Trust the MessageRouter
orchestrator = Orchestrator()
# MessageRouter is created and started automatically

# Avoid: Manually managing message routing
# (not needed, handled by framework)
```

### 2. Mark Terminated Agents Promptly

```python
# Good: Mark agents as terminated immediately
def on_agent_terminated(agent_name, **kwargs):
    orchestrator.message_router.mark_agent_terminated(agent_name)

orchestrator.event_bus.register_callback(
    OrchestratorEvent.AGENT_TERMINATED,
    on_agent_terminated
)
```

### 3. Monitor Router Health in Production

```python
# Check if MessageRouter thread is alive
if not orchestrator.message_router._thread.is_alive():
    logger.critical("MessageRouter thread died!")
    # Take recovery action
```

## Debugging

### Enable Debug Logging

```python
import logging
logging.getLogger("PyOrchestrate.MessageRouter").setLevel(logging.DEBUG)
```

This shows:
- Every message received
- Event translations
- Filtered messages
- Errors and warnings

### Inspect Terminated Agents

```python
# See which agents are being filtered
terminated = orchestrator.message_router._terminated_agents
print(f"Filtering messages from: {terminated}")
```

## See Also

- [OrchestratorEventBus](./event-bus.md) - Receives translated events
- [MessageChannel](../utilities/message-channel.md) - Low-level message transport
- [AgentLifecycleManager](./lifecycle-manager.md) - Creates agents with MessageChannel
- [Orchestrator Internals](./index.md) - Architecture overview
