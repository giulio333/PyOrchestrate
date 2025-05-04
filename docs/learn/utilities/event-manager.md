---
title: Event Manager
editLink: true
---

# Event Manager

The **Event Manager** is a core utility in PyOrchestrate that provides a centralized event handling mechanism. It enables decoupled communication between components through a publisher-subscriber pattern.

## Overview

The EventManager maintains a registry of event listeners (callbacks) that are executed when specific events are emitted. Key features include:

- Event registration and callback attachment
- Asynchronous event emission using a thread pool
- Safe execution that isolates errors in individual callbacks
- Automatic addition of timestamp data to events

This component is fundamental to PyOrchestrate's event-driven architecture, allowing Agents and the Orchestrator to communicate without direct coupling.

## Core Concepts

### Events

Events in PyOrchestrate are typically defined as Enum classes, providing a type-safe way to identify different event types. For example:

```python
from enum import Enum

class AgentEvent(Enum):
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_ERROR = "agent_error"
```

### Event Manager

The `EventManager` class manages the registration and emission of events:

```python
from PyOrchestrate.core.utilities.event_manager import EventManager
from enum import Enum

# Define events
class MyEvents(Enum):
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"

# Initialize event manager
event_manager = EventManager()
```

## Using the Event Manager

### Registering Event Handlers

You can register callback functions to be executed when specific events are emitted:

```python
# Define a callback function
def on_task_started(task_name, **kwargs):
    print(f"Task {task_name} started at {kwargs.get('event_time')}")

# Register the callback for the event
event_manager.register_event(MyEvents.TASK_STARTED, on_task_started)
```

### Emitting Events

To trigger an event and execute all registered callbacks:

```python
# Emit an event with custom parameters
event_manager.emit(MyEvents.TASK_STARTED, task_name="data_processing")
```

The EventManager automatically adds timestamp information:
- `event_date`: ISO formatted date when the event was emitted
- `event_time`: ISO formatted time when the event was emitted

### Complete Example

Here's a complete example demonstrating the EventManager usage:

```python
from enum import Enum
from PyOrchestrate.core.utilities.event_manager import EventManager

# Define your events
class MyEvents(Enum):
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

# Create callback functions
def on_task_started(task_name, **kwargs):
    print(f"Task {task_name} started at {kwargs.get('event_time')}")

def on_task_completed(task_name, result, **kwargs):
    print(f"Task {task_name} completed with result: {result}")

def on_task_failed(task_name, error, **kwargs):
    print(f"Task {task_name} failed with error: {error}")

# Initialize the event manager
event_manager = EventManager()

# Register events and callbacks
event_manager.register_event(MyEvents.TASK_STARTED, on_task_started)
event_manager.register_event(MyEvents.TASK_COMPLETED, on_task_completed)
event_manager.register_event(MyEvents.TASK_FAILED, on_task_failed)

# Emit events
event_manager.emit(MyEvents.TASK_STARTED, task_name="data_processing")
event_manager.emit(MyEvents.TASK_COMPLETED, task_name="data_processing", result="success")
event_manager.emit(MyEvents.TASK_FAILED, task_name="data_processing", error="timeout")

# Shutdown when done
event_manager.shutdown()
```

## Integration with Agents and Orchestrator

Both Agents and the Orchestrator use the EventManager internally to handle state transitions and communicate with each other.

### Agent Event Handling

The EventManager powers the Agent's state event system:

```python
from PyOrchestrate.core.agent.events import AgentStateEvent

# Register handler for agent events
orchestrator.event_manager.register_event(
    AgentStateEvent.STARTED, 
    lambda agent_name, **kwargs: print(f"Agent {agent_name} started at {kwargs.get('event_time')}")
)
```

### Orchestrator Event Handling

Similarly, you can register handlers for Orchestrator events:

```python
from PyOrchestrate.core.orchestrator.events import OrchestratorEvent

# Register handler for orchestrator events
orchestrator.event_manager.register_event(
    OrchestratorEvent.ALL_AGENTS_TERMINATED,
    lambda **kwargs: print(f"All agents terminated at {kwargs.get('event_time')}")
)
```

## Implementation Details

### Parameter Filtering

The EventManager automatically filters parameters based on each callback's signature, passing only the parameters that the callback accepts. This makes it flexible and easy to use without worrying about parameter compatibility.

### Thread Pool

Event callbacks are executed asynchronously using a thread pool executor. This ensures that event emission does not block the main thread and that slow callbacks do not affect the performance of other callbacks.

### Error Isolation

Exceptions in one callback are caught and logged, preventing them from affecting the execution of other callbacks for the same event.

### Shutdown

When your application is done using the EventManager, you should call the `shutdown()` method to properly clean up resources:

```python
event_manager.shutdown()
```

This method is also automatically registered with Python's `atexit` module to ensure proper cleanup when the application terminates.