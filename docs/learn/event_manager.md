# EventManager Module

## Overview

The `EventManager` module provides a centralized event-handling mechanism for the application. It manages event registration, callback attachment, and event emission with built-in error isolation.

## Key Features

### Event Registration

The `register_event` method allows you to register new events.

### Attaching Callbacks

The `connect` method lets you attach callback functions to events.

### Emitting Events

The `emit` method allows you to emit events and pass arguments to the callbacks.

### Exception Handling

The `EventManager` handles exceptions in callbacks to prevent failure propagation.

## Usage Guide

### Initializing an EventManager Instance

To initialize an `EventManager` instance:

```python
from event_manager import EventManager

event_manager = EventManager()
```

### Registering New Events

You can register new events using Enums:

```python
from enum import Enum

class MyEvents(Enum):
    EVENT_ONE = "event_one"
    EVENT_TWO = "event_two"

event_manager.register_event(MyEvents.EVENT_ONE)
event_manager.register_event(MyEvents.EVENT_TWO)
```

### Connecting Callback Functions

To connect callback functions to events:

```python
def callback_function(data):
    print(f"Callback received data: {data}")

event_manager.connect(MyEvents.EVENT_ONE, callback_function)
```

### Emitting Events

To emit events and pass arguments to callbacks:

```python
event_manager.emit(MyEvents.EVENT_ONE, data="Hello, World!")
```

## Code Examples

### Registering and Emitting Events

```python
from event_manager import EventManager
from enum import Enum

class MyEvents(Enum):
    EVENT_ONE = "event_one"

event_manager = EventManager()
event_manager.register_event(MyEvents.EVENT_ONE)

def callback_function(data):
    print(f"Callback received data: {data}")

event_manager.connect(MyEvents.EVENT_ONE, callback_function)
event_manager.emit(MyEvents.EVENT_ONE, data="Hello, World!")
```

### Attaching Multiple Listeners

```python
def callback_one(data):
    print(f"Callback One received data: {data}")

def callback_two(data):
    print(f"Callback Two received data: {data}")

event_manager.connect(MyEvents.EVENT_ONE, callback_one)
event_manager.connect(MyEvents.EVENT_ONE, callback_two)
event_manager.emit(MyEvents.EVENT_ONE, data="Hello, World!")
```

### Error Isolation

```python
def faulty_callback(data):
    raise ValueError("An error occurred")

def safe_callback(data):
    print(f"Safe callback received data: {data}")

event_manager.connect(MyEvents.EVENT_ONE, faulty_callback)
event_manager.connect(MyEvents.EVENT_ONE, safe_callback)
event_manager.emit(MyEvents.EVENT_ONE, data="Hello, World!")
```

## Design Considerations

### Event Storage

Events are stored as dictionary entries for efficient lookup and management.

### Argument Filtering

Keyword arguments are filtered based on function signatures to ensure compatibility.

### Thread Safety

The current implementation does not include explicit thread synchronization.

## Potential Improvements

### Asynchronous Callbacks

Adding support for asynchronous callbacks.

### Prioritized Execution

Providing an option for prioritized execution of listeners.

### Event Unregistration

Enabling event unregistration.
