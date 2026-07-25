---
mode: agent
---
# PR #69: Orchestrator Refactoring - Documentation Guide

## Overview

This Pull Request represents a major architectural refactoring of the PyOrchestrate `Orchestrator` class, transforming it from a monolithic component (~800 lines) into a clean **Facade Pattern** implementation (~520 lines) that delegates responsibilities to six specialized manager classes.

The refactoring improves:
- **Code maintainability**: Each manager has a single, focused responsibility
- **Testability**: 85 new unit tests added for manager classes
- **Scalability**: New features can be added to specific managers without touching Orchestrator
- **Clarity**: Clear separation of concerns makes the codebase easier to understand

---

## Architecture: From Monolithic to Modular

### Before: Monolithic Orchestrator

The original `Orchestrator` class handled everything:
- Dependency graph management and validation
- Agent lifecycle (registration, starting, stopping)
- Worker pool scheduling and concurrency limits
- Message routing from agents to event system
- Event management and callback execution
- Command interface for external CLI control

This made the class difficult to maintain, test, and extend.

### After: Facade Pattern with Specialized Managers

The refactored `Orchestrator` now acts as a **facade** that coordinates six specialized managers:

```python
class Orchestrator(BaseClass):
    def __init__(self, ...):
        # Specialized managers
        self.dependency_graph = DependencyGraph()
        self.lifecycle_manager = AgentLifecycleManager(...)
        self.worker_pool = WorkerPoolScheduler(...)
        self.event_bus = OrchestratorEventBus(...)
        self.message_router = MessageRouter(...)
        self.command_interface = CommandInterface(...)  # Optional
```

Each manager is independently testable and handles a specific domain of responsibility.

---

## The Six Specialized Managers

### 1. DependencyGraph

**Responsibility**: Manages agent dependencies and ensures correct startup order.

**Key Features**:
- Validates dependency graph for cycles and missing agents
- Performs topological sorting to determine startup order
- Raises `ValueError` on circular dependencies or unregistered agents

**Usage Pattern**:
```python
orchestrator.add_dependency("AgentB", ["AgentA"])  # AgentB depends on AgentA
orchestrator.validate_dependencies()  # Checks for cycles and missing agents
ordered_agents = orchestrator.dependency_graph.topological_sort(agent_names)
```

**Implementation Details**:
- Uses depth-first search (DFS) for cycle detection
- Maintains `_dependencies` dict mapping agent → list of dependencies
- Validates against registered agent names in `OMemory`

---

### 2. AgentLifecycleManager

**Responsibility**: Manages the complete lifecycle of agents (registration, creation, stopping).

**Key Features**:
- Registers agents with their configurations and plugins
- Creates agent instances (Process or Thread) with proper event wiring
- Handles graceful shutdown of all agents
- Tracks agent state in `OMemory`

**Usage Pattern**:
```python
# Register agent
agent_entry = lifecycle_manager.register_agent(
    agent_class=MyAgent,
    name="worker1",
    custom_config=MyAgent.Config(interval=5.0)
)

# Stop all agents
lifecycle_manager.stop_all()
```

**Implementation Details**:
- Creates `AgentEntry` objects stored in `OMemory.agents`
- Wires up `StateEvents` and `ControlEvents` for agent lifecycle
- Handles both process and thread-based agents
- Injects message channel for orchestrator communication

---

### 3. WorkerPoolScheduler

**Responsibility**: Enforces concurrency limits and manages agent startup queue.

**Key Features**:
- Limits concurrent running agents via `max_workers` configuration
- Queues agents when pool is full, starts them when slots become available
- Tracks agent states: pending → running → completed
- Provides `all_finished` property for orchestrator join logic

**Usage Pattern**:
```python
# Configure max concurrent agents
config = OrchestratorConfig(max_workers=5)

# Start agent (may queue if pool is full)
worker_pool.start_agent("agent_name")

# Notify when agent terminates (automatically starts next queued)
worker_pool.on_agent_terminated("agent_name")

# Check if all agents completed
if worker_pool.all_finished:
    print("All agents done!")
```

**Implementation Details**:
- Uses `_pending_queue` (deque) for agents waiting to start
- Tracks `_running_agents` (set) for currently executing agents
- Enforces `agent_start_timeout` configuration
- Automatically starts next queued agent on termination

---

### 4. OrchestratorEventBus

**Responsibility**: Unified facade for event management and history tracking.

**Key Features**:
- Combines `EventManager` (callbacks) and `EventStore` (history) into single interface
- Automatically records events to history when emitted
- Supports event policies for selective storage (e.g., keep only last 2 heartbeats)
- Provides query interface for event history

**Usage Pattern**:
```python
# Register callback for agent events
orchestrator.event_bus.register_callback(
    OrchestratorEvent.AGENT_STARTED,
    lambda agent_name, **kwargs: print(f"{agent_name} started!")
)

# Emit event (automatically recorded to history)
orchestrator.event_bus.emit(
    OrchestratorEvent.AGENT_STARTED,
    agent_name="worker1"
)

# Query history
recent_events = orchestrator.event_bus.event_store.query(
    category="agent",
    event_name="AGENT_STARTED"
)
```

**Implementation Details**:
- `EventManager` handles callback registration and execution
- `EventStore` maintains ring buffer of events with configurable capacity
- Supports `EventPolicy` for custom retention rules (e.g., `BucketRingStore`)
- Thread-safe implementation for concurrent access

---

### 5. MessageRouter

**Responsibility**: Routes agent messages to orchestrator event system.

**Key Features**:
- Receives messages from agents via `MessageChannel`
- Translates agent events to orchestrator events
- Filters messages from terminated agents
- Manages own `ChannelHandler` lifecycle

**Usage Pattern**:
```python
# MessageRouter started automatically in Orchestrator.__init__
message_router.start()

# Agent sends message
agent.send_message(ServiceMessage.create_status(
    sender="worker1",
    status="success",
    event_name=AgentEvent.AGENT_READY.value
))

# MessageRouter receives and converts to OrchestratorEvent.AGENT_READY

# Mark agent as terminated (stops processing its messages)
message_router.mark_agent_terminated("worker1")

# Cleanup
message_router.stop(timeout=2.0)
```

**Implementation Details**:
- Uses `ChannelHandler` to listen on process-based `MessageChannel`
- Maps `AgentEvent` → `OrchestratorEvent` using `_event_type_mapping`
- Maintains `_terminated_agents` set to filter stale messages
- Runs in background thread for non-blocking message processing

---

### 6. CommandInterface

**Responsibility**: Provides external CLI control via ZMQ socket.

**Key Features**:
- Exposes orchestrator commands over ZMQ REQ/REP socket
- Supports commands: `ps`, `status`, `stats`, `shutdown`, `history`
- Configurable command whitelist for security
- Tracks command execution in event history

**Usage Pattern**:
```python
# Enable in orchestrator config
config = OrchestratorConfig(
    enable_command_interface=True,
    command_zmq_address="tcp://127.0.0.1:5570",
    allowed_commands="basic"  # or "all", or set{"ps", "status"}
)

# CLI sends command via ZMQ
# pyorchestrate ps

# CommandInterface receives and executes
command_interface.handle_command({
    "command": "ps",
    "args": []
})

# Response: {"status": "success", "data": {"agents": [...]}}
```

**Implementation Details**:
- Uses `zmq.REP` socket for request/response pattern
- Command presets: `"basic"`, `"monitoring"`, `"all"`
- Manages own `ChannelHandler` for ZMQ socket polling
- Graceful shutdown with `stop(timeout=2.0)`
- Records command execution to `EventStore`

**Security Considerations**:
- Default: Only basic commands allowed (`ps`, `status`)
- Set `allowed_commands=None` for unrestricted access (use with caution)
- Set `allowed_commands={"ps"}` for custom whitelist

---

## Communication Flow

### Agent → Orchestrator Message Flow

```
Agent
  ↓ ServiceMessage via MessageChannel (process-safe queue)
MessageRouter (ChannelHandler thread)
  ↓ Converts AgentEvent → OrchestratorEvent
OrchestratorEventBus
  ├─→ EventManager (executes registered callbacks)
  └─→ EventStore (records to history)
```

**Example**: Agent ready notification
1. Agent calls `_handle_ready()` → sends `AgentEvent.AGENT_READY`
2. MessageRouter receives message, emits `OrchestratorEvent.AGENT_READY`
3. EventBus executes callbacks and records to history
4. User callback receives `(agent_name="worker1", event_date=..., event_time=...)`

### CLI → Orchestrator Command Flow

```
CLI Tool (pyorchestrate ps)
  ↓ ZMQ REQ socket
CommandInterface (ChannelHandler thread)
  ↓ Validates command against allowed_commands
  ↓ Executes command method
  ↓ Records execution to EventStore
  ↓ ZMQ REP socket
CLI Tool (receives JSON response)
```

---

## Lifecycle and Initialization Order

### Orchestrator Startup Sequence

1. **Initialization** (`__init__`):
   ```python
   memory = OMemory()  # Agent storage
   msg_channel = MessageChannel("process")  # Agent communication
   event_bus = OrchestratorEventBus(event_store)  # Event system
   dependency_graph = DependencyGraph()  # Dependency tracking
   lifecycle_manager = AgentLifecycleManager(...)  # Agent lifecycle
   worker_pool = WorkerPoolScheduler(...)  # Concurrency control
   message_router = MessageRouter(...)  # Message routing
   command_interface = CommandInterface(...)  # CLI control (optional)
   ```

2. **Channel Handler Startup** (automatic in `__init__`):
   ```python
   message_router.start()  # Starts background thread
   command_interface.start()  # Starts ZMQ listener (if enabled)
   ```

3. **Agent Registration** (user code):
   ```python
   orchestrator.register_agent(MyAgent, "worker1")
   orchestrator.add_dependency("worker2", ["worker1"])
   ```

4. **Orchestrator Start** (`start()`):
   ```python
   validate_dependencies()  # Check for cycles
   ordered_agents = dependency_graph.topological_sort(...)  # Get startup order
   for agent in ordered_agents:
       worker_pool.start_agent(agent)  # Start or queue
   ```

5. **Orchestrator Join** (`join()`):
   - Monitor agent termination
   - Notify worker_pool on completion
   - Continue until `RunMode` condition met
   - Shutdown channel handlers
   - Finalize plugins

### Agent Lifecycle States

```
REGISTERED → QUEUED → RUNNING → TERMINATED
     ↑          ↑         ↑          ↓
     |          |         |    (recorded by MessageRouter)
     |          |    (started by WorkerPoolScheduler)
     |     (queued by WorkerPoolScheduler if pool full)
(via lifecycle_manager.register_agent)
```

---

## Configuration Examples

### Basic Setup (Default Behavior)

```python
from PyOrchestrate.core.orchestrator import Orchestrator, RunMode

orchestrator = Orchestrator()  # Uses default config
# - max_workers: 10
# - run_mode: STOP_ON_EMPTY (stops when all agents done)
# - enable_command_interface: False
# - history_max_events: 1000

orchestrator.register_agent(MyAgent, "worker")
orchestrator.start()
orchestrator.join()  # Blocks until all agents complete
```

### Advanced Setup (Daemon Mode with CLI)

```python
config = Orchestrator.Config(
    max_workers=5,  # Max 5 concurrent agents
    run_mode=RunMode.DAEMON,  # Keep running until explicit shutdown
    enable_command_interface=True,  # Enable CLI control
    command_zmq_address="tcp://127.0.0.1:5570",
    allowed_commands="all",  # Allow all commands
    history_max_events=5000,  # Store more history
    history_payload_bytes=10000  # Larger payloads
)

orchestrator = Orchestrator(config=config)

# Register agents with dependencies
orchestrator.register_agent(DataCollector, "collector")
orchestrator.register_agent(DataProcessor, "processor", 
    custom_config=DataProcessor.Config(batch_size=100))
orchestrator.add_dependency("processor", ["collector"])

orchestrator.start()
orchestrator.join()  # Runs indefinitely until CLI shutdown command
```

### Custom Event Policies

```python
from PyOrchestrate.core.orchestrator import EventStore, BucketRingStore

# Custom retention: keep only last 2 heartbeats per agent
event_store = EventStore(
    capacity=1000,
    event_policies={
        "AGENT_HEARTBEAT": BucketRingStore(capacity=2)
    }
)

orchestrator = Orchestrator()
orchestrator.event_bus = OrchestratorEventBus(event_store)
```

---

## Testing Approach

Each manager has dedicated unit tests with mocked dependencies:

### Example: Testing WorkerPoolScheduler

```python
def test_worker_pool_respects_max_workers(self):
    """Pool should queue agents when max_workers reached"""
    lifecycle_manager = MagicMock()
    worker_pool = WorkerPoolScheduler(
        max_workers=2,
        lifecycle_manager=lifecycle_manager,
        logger=MagicMock()
    )
    
    # Start 3 agents (max_workers=2)
    worker_pool.start_agent("agent1")
    worker_pool.start_agent("agent2")
    worker_pool.start_agent("agent3")  # Should be queued
    
    # Verify only 2 started
    assert lifecycle_manager.start_agent.call_count == 2
    assert len(worker_pool._pending_queue) == 1
    assert "agent3" in worker_pool._pending_queue
    
    # Terminate one, next should start
    worker_pool.on_agent_terminated("agent1")
    assert lifecycle_manager.start_agent.call_count == 3
```

**Test Coverage**:
- DependencyGraph: 14 tests (cycles, missing agents, topological sort)
- AgentLifecycleManager: 15 tests (registration, starting, stopping)
- WorkerPoolScheduler: 18 tests (concurrency, queuing, timeouts)
- MessageRouter: 20 tests (routing, filtering, lifecycle)
- OrchestratorEventBus: 18 tests (callbacks, history, policies)
- CommandInterface: 16 tests (commands, validation, ZMQ lifecycle)

**Total**: 85 new tests, 174 tests passing overall

---

## Migration Notes for Existing Code

### Breaking Changes: NONE

The refactoring maintains full backward compatibility with the public API. All existing code continues to work without modifications.

### Removed Compatibility Properties (Post-Refactoring)

The following properties were temporarily added for compatibility but have been removed:

```python
# REMOVED - Use event_bus instead
orchestrator.event_store  # Use: orchestrator.event_bus.event_store
orchestrator.event_manager  # Use: orchestrator.event_bus.event_manager
```

### Recommended Access Patterns

```python
# Event management
orchestrator.event_bus.register_callback(event_type, callback)
orchestrator.event_bus.emit(event_type, **kwargs)

# Event history
orchestrator.event_bus.event_store.query(category="agent")
orchestrator.event_bus.event_store.record(category, event_name, severity, data)

# Agent management
orchestrator.register_agent(AgentClass, "name")
orchestrator.add_dependency("agent2", ["agent1"])
orchestrator.start()

# Worker pool status
if orchestrator.worker_pool.all_finished:
    print("All agents completed")
```

---

## Additional Refactoring: BaseClass.validate_config

As part of this PR, the `validate_config()` method was extracted from both `BaseAgent` and `Orchestrator` and moved to the base `BaseClass`, eliminating code duplication.

**Implementation** (in `BaseClass`):
```python
@final
def validate_config(self):
    """Validates the configuration."""
    try:
        self.config._validate()
    except ConfigValidationError as e:
        self.logger.error(e)
        raise e
    except ConfigValidationWarning as w:
        self.logger.warning(w)
    self.logger.debug("Self configuration validated.")
```

**Benefits**:
- DRY: Single implementation inherited by all subclasses
- Enhanced handling: Separate error and warning handling
- Consistency: Uniform validation behavior across framework

---

## Key Takeaways for Documentation

1. **Architecture**: Emphasize the Facade Pattern and single-responsibility principle
2. **Manager Roles**: Clearly explain what each manager does and when to interact with it
3. **Communication**: Detail the message flow (Agent → MessageRouter → EventBus)
4. **CLI Control**: Explain CommandInterface setup and security considerations
5. **Testing**: Highlight the improved testability with 85 new unit tests
6. **Migration**: Reassure users that existing code continues to work unchanged
7. **Advanced Usage**: Show custom configurations and event policies

---

## Suggested Documentation Structure

```
Advanced: Orchestrator Internals
├── Overview: From Monolithic to Modular
├── Architecture Diagram (optional visual)
├── The Six Managers
│   ├── DependencyGraph
│   ├── AgentLifecycleManager
│   ├── WorkerPoolScheduler
│   ├── OrchestratorEventBus
│   ├── MessageRouter
│   └── CommandInterface
├── Communication Flows
│   ├── Agent → Orchestrator (Messages)
│   └── CLI → Orchestrator (Commands)
├── Lifecycle and Initialization
├── Configuration Examples
│   ├── Basic Setup
│   ├── Daemon Mode with CLI
│   └── Custom Event Policies
└── Testing and Extensibility
```

---

## Code Statistics

- **Lines removed from Orchestrator**: ~280 lines
- **New manager classes**: 6 classes (~1,200 lines total)
- **New unit tests**: 85 tests (~1,600 lines)
- **Documentation files**: 6 markdown files
- **Test success rate**: 174/174 passing (100%)

---

## Related Files for Reference

- `PyOrchestrate/core/orchestrator/dependency_graph.py`
- `PyOrchestrate/core/orchestrator/lifecycle_manager.py`
- `PyOrchestrate/core/orchestrator/worker_pool.py`
- `PyOrchestrate/core/orchestrator/event_bus.py`
- `PyOrchestrate/core/orchestrator/message_router.py`
- `PyOrchestrate/core/orchestrator/command_interface.py`
- `PyOrchestrate/core/orchestrator/orchestrator.py` (refactored)
- `test/test_dependency_graph.py` through `test/test_command_interface.py`

---

**End of Documentation Guide**
