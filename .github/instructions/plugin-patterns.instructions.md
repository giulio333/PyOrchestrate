---
applyTo: "PyOrchestrate/core/plugins/**/*.py"
description: "Plugin system patterns, protocols, and lifecycle management for PyOrchestrate"
---

# Plugin System Pattern Rules

## Core Concept

Plugins extend agent functionality using the **Inner Class Pattern** - NOT manual registration.

## Plugin Inner Class Pattern

### Basic Structure
```python
from PyOrchestrate.core.agent import PeriodicProcessAgent
from PyOrchestrate.core.plugins import ZeroMQPubSub
import zmq

class MyAgent(PeriodicProcessAgent):
    class Plugin(PeriodicProcessAgent.Plugin):
        # Define plugins as class attributes
        zmq_pub = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
        zmq_pair = ZeroMQPair("tcp://*:5556", bind=True)
    
    plugin: Plugin  # Type annotation REQUIRED
    
    def setup(self):
        super().setup()
        # Plugins automatically initialized
    
    def runner(self):
        super().runner()
        # Access via self.plugin
        self.plugin.zmq_pub.send(b"Hello")
```

**Validation:**
- [ ] Plugin is inner class, not manual registration
- [ ] Inherits from parent agent's Plugin class
- [ ] Agent has `plugin: Plugin` type annotation
- [ ] Access via `self.plugin.plugin_name`
- [ ] No `register_plugin()` calls

## Plugin Protocol

All plugins must implement `PluginProtocol`:

```python
from PyOrchestrate.core.plugins.plugin_protocols import PluginProtocol

class CustomPlugin(PluginProtocol):
    def setup(self) -> None:
        """Initialize plugin resources"""
        pass
    
    def teardown(self) -> None:
        """Clean up plugin resources"""
        pass
    
    def is_ready(self) -> bool:
        """Check if plugin is ready to use"""
        return True
```

**Validation:**
- [ ] Implements all PluginProtocol methods
- [ ] `setup()` initializes resources
- [ ] `teardown()` cleans up resources
- [ ] `is_ready()` returns accurate status
- [ ] Thread-safe if used in ThreadAgent

## Plugin Lifecycle

### Initialization Flow
1. Agent instantiated with Plugin inner class
2. Agent's `setup()` calls `super().setup()`
3. Framework automatically calls plugin `setup()` methods
4. Plugin resources initialized
5. Agent can use plugins via `self.plugin.plugin_name`

### Cleanup Flow
1. Agent's `on_stop()` called
2. Framework automatically calls plugin `teardown()` methods
3. Plugin resources cleaned up
4. Agent terminates

**Validation:**
- [ ] Plugin `setup()` called automatically
- [ ] Plugin `teardown()` called automatically
- [ ] No manual lifecycle management needed
- [ ] Proper resource cleanup guaranteed

## ZeroMQ Communication Plugins

### Available ZeroMQ Plugins
```python
from PyOrchestrate.core.plugins.com import (
    ZeroMQPubSub,      # Publish-Subscribe pattern
    ZeroMQPushPull,    # Push-Pull (load balancing)
    ZeroMQReqRep,      # Request-Reply
    ZeroMQPair,        # Pair (1-to-1)
    ZeroMQRouterDealer,# Router-Dealer (advanced)
)
```

### PubSub Pattern
```python
class Publisher(PeriodicProcessAgent):
    class Plugin(PeriodicProcessAgent.Plugin):
        pub = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
    
    plugin: Plugin
    
    def runner(self):
        super().runner()
        self.plugin.pub.send(b"message")

class Subscriber(LoopingProcessAgent):
    class Plugin(LoopingProcessAgent.Plugin):
        sub = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB)
    
    plugin: Plugin
    
    def execute(self):
        super().execute()
        msg = self.plugin.sub.receive()
        if msg:
            self.logger.info(f"Received: {msg}")
```

**Validation:**
- [ ] Correct socket types (PUB/SUB, PUSH/PULL, etc.)
- [ ] Proper address binding/connection
- [ ] Message serialization handled
- [ ] Non-blocking receive in loops

### Push-Pull Pattern
```python
class Producer(PeriodicProcessAgent):
    class Plugin(PeriodicProcessAgent.Plugin):
        push = ZeroMQPushPull("tcp://*:5556", zmq.PUSH)
    
    plugin: Plugin

class Worker(LoopingProcessAgent):
    class Plugin(LoopingProcessAgent.Plugin):
        pull = ZeroMQPushPull("tcp://localhost:5556", zmq.PULL)
    
    plugin: Plugin
```

**Validation:**
- [ ] Producer uses PUSH socket
- [ ] Worker uses PULL socket
- [ ] Load balancing understood
- [ ] Work distribution appropriate

### Request-Reply Pattern
```python
class Server(LoopingProcessAgent):
    class Plugin(LoopingProcessAgent.Plugin):
        rep = ZeroMQReqRep("tcp://*:5557", zmq.REP)
    
    plugin: Plugin
    
    def execute(self):
        super().execute()
        request = self.plugin.rep.receive()
        if request:
            response = self.process(request)
            self.plugin.rep.send(response)

class Client(PeriodicProcessAgent):
    class Plugin(PeriodicProcessAgent.Plugin):
        req = ZeroMQReqRep("tcp://localhost:5557", zmq.REQ)
    
    plugin: Plugin
    
    def runner(self):
        super().runner()
        self.plugin.req.send(b"request")
        response = self.plugin.req.receive()
```

**Validation:**
- [ ] REQ/REP alternation maintained
- [ ] No simultaneous sends on REQ
- [ ] Server responds to all requests
- [ ] Client handles timeouts

## Heartbeat Plugin

### HeartbeatPlugin Pattern
```python
from PyOrchestrate.core.plugins.heartbeat import HeartbeatPlugin

class MyAgent(PeriodicProcessAgent):
    class Plugin(PeriodicProcessAgent.Plugin):
        heartbeat = HeartbeatPlugin(interval=5.0)
    
    plugin: Plugin
    
    def runner(self):
        super().runner()
        # Heartbeat automatically sent
        # Check if alive
        if self.plugin.heartbeat.is_alive():
            self.logger.info("Still alive")
```

**Validation:**
- [ ] Heartbeat interval appropriate
- [ ] `is_alive()` checked regularly
- [ ] Timeout handling implemented
- [ ] Cleanup in teardown

## Thread Safety Considerations

### For ThreadAgents
Plugins in ThreadAgents share memory:

```python
import threading

class ThreadSafePlugin(PluginProtocol):
    def __init__(self):
        self._lock = threading.Lock()
        self._data = {}
    
    def set_data(self, key, value):
        with self._lock:
            self._data[key] = value
    
    def get_data(self, key):
        with self._lock:
            return self._data.get(key)
```

**Validation:**
- [ ] Locks used for shared state
- [ ] Thread-safe data structures
- [ ] No race conditions
- [ ] Deadlock prevention

### For ProcessAgents
Plugins in ProcessAgents are isolated:
- Each process has independent plugin instance
- No shared memory concerns
- Communication via ZeroMQ only

**Validation:**
- [ ] No assumptions about shared state
- [ ] Inter-process communication explicit
- [ ] Serialization handled properly

## Plugin Manager

The PluginManager (internal) handles:
- Plugin discovery from inner classes
- Automatic setup/teardown orchestration
- Plugin dependency resolution
- Error handling during lifecycle

**Don't interact with PluginManager directly** - framework handles it.

**Validation:**
- [ ] No direct PluginManager usage
- [ ] Trust framework lifecycle management
- [ ] Plugins defined via inner class only

## Custom Plugin Development

### Creating a Custom Plugin
```python
from PyOrchestrate.core.plugins.plugin_protocols import PluginProtocol

class DatabasePlugin(PluginProtocol):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
    
    def setup(self) -> None:
        """Connect to database"""
        import psycopg2
        self.connection = psycopg2.connect(self.connection_string)
    
    def teardown(self) -> None:
        """Close connection"""
        if self.connection:
            self.connection.close()
    
    def is_ready(self) -> bool:
        """Check connection"""
        return self.connection is not None
    
    def query(self, sql: str):
        """Execute query"""
        cursor = self.connection.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

# Usage
class DataAgent(PeriodicProcessAgent):
    class Plugin(PeriodicProcessAgent.Plugin):
        db = DatabasePlugin("postgresql://localhost/mydb")
    
    plugin: Plugin
    
    def runner(self):
        super().runner()
        results = self.plugin.db.query("SELECT * FROM users")
```

**Validation:**
- [ ] Implements PluginProtocol
- [ ] Constructor parameters documented
- [ ] Resource acquisition in `setup()`
- [ ] Resource release in `teardown()`
- [ ] Error handling in methods
- [ ] Thread-safe if needed

## Common Anti-Patterns to Avoid

### ❌ DON'T: Manual Plugin Registration
```python
# WRONG
agent = MyAgent()
agent.register_plugin("zmq", ZeroMQPubSub(...))
```

### ✅ DO: Inner Class Pattern
```python
# CORRECT
class MyAgent(BaseAgent):
    class Plugin(BaseAgent.Plugin):
        zmq = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
    
    plugin: Plugin
```

### ❌ DON'T: Manual Setup/Teardown
```python
# WRONG
def setup(self):
    super().setup()
    self.plugin.zmq.setup()  # Framework does this!
```

### ✅ DO: Trust Framework
```python
# CORRECT
def setup(self):
    super().setup()
    # Plugins already set up by framework
    # Just use them
    self.plugin.zmq.send(b"ready")
```

### ❌ DON'T: Access Before Setup
```python
# WRONG
class MyAgent(BaseAgent):
    class Plugin(BaseAgent.Plugin):
        zmq = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
    
    plugin: Plugin
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plugin.zmq.send(b"too early!")  # Not set up yet!
```

### ✅ DO: Wait for Setup
```python
# CORRECT
class MyAgent(BaseAgent):
    class Plugin(BaseAgent.Plugin):
        zmq = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
    
    plugin: Plugin
    
    def setup(self):
        super().setup()
        # Now plugins are ready
        self.plugin.zmq.send(b"ready!")
```

### ❌ DON'T: Forget Type Annotation
```python
# WRONG
class MyAgent(BaseAgent):
    class Plugin(BaseAgent.Plugin):
        zmq = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
    
    # Missing: plugin: Plugin
```

### ✅ DO: Add Type Annotation
```python
# CORRECT
class MyAgent(BaseAgent):
    class Plugin(BaseAgent.Plugin):
        zmq = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
    
    plugin: Plugin  # Required!
```

## Testing Patterns

### Testing Plugins
```python
import unittest
from unittest.mock import MagicMock, patch

class TestCustomPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = DatabasePlugin("test_connection")
    
    @patch('psycopg2.connect')
    def test_setup(self, mock_connect):
        mock_connect.return_value = MagicMock()
        self.plugin.setup()
        self.assertTrue(self.plugin.is_ready())
        mock_connect.assert_called_once()
    
    def test_teardown(self):
        self.plugin.connection = MagicMock()
        self.plugin.teardown()
        self.plugin.connection.close.assert_called_once()
```

**Validation:**
- [ ] Tests cover setup/teardown
- [ ] Tests verify is_ready()
- [ ] Tests check error handling
- [ ] Integration tests for ZeroMQ plugins

## Reference Examples

Always consult these examples:
- `examples/communication/example_zmq_pubsub.py` - PubSub pattern
- `examples/communication/example_zmq_pushpull.py` - Push-Pull pattern
- `examples/communication/example_zmq_reqrep.py` - Request-Reply pattern
- `examples/example_heartbeat_agent.py` - Heartbeat plugin
- `test/test_communication_plugin.py` - Plugin testing patterns
