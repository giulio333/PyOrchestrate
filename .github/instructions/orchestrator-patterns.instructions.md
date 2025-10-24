---
applyTo: "PyOrchestrate/core/orchestrator/**/*.py"
description: "Orchestrator patterns, event system, and dependency management for PyOrchestrate"
---

# Orchestrator Pattern Rules

## Core Responsibilities

The Orchestrator is the **container manager** for agents - think "Docker for Python processes":
1. Agent lifecycle management (create, monitor, cleanup)
2. Event system coordination
3. Dependency chain management
4. Memory tracking and resource management
5. Message channel coordination

## Agent Registration Patterns

### Basic Registration
```python
orchestrator = Orchestrator()
orchestrator.register_agent(MyAgent, "agent_name")
```

### With Custom Configuration
```python
orchestrator.register_agent(
    MyAgent,
    "agent_name",
    custom_config=MyAgent.Config(
        execution_interval=0.2,
        custom_field="value"
    )
)
```

**Validation:**
- [ ] Agent class passed (not instance)
- [ ] Unique agent names
- [ ] Custom config matches agent's Config class
- [ ] Registration before `orchestrator.start()`

## Event System Architecture

### Event-Driven Communication
**CRITICAL**: Agents communicate via MessageChannel to Orchestrator - **NEVER directly between agents**

### Event Registration
```python
from PyOrchestrate.core.utilities import OrchestratorEvent

# Register callbacks on Orchestrator
orchestrator.register_event(
    OrchestratorEvent.AGENT_READY, 
    on_agent_ready_callback
)
orchestrator.register_event(
    OrchestratorEvent.AGENT_STARTED, 
    on_agent_started_callback
)
orchestrator.register_event(
    OrchestratorEvent.AGENT_TERMINATED, 
    on_agent_stopped_callback
)

def on_agent_ready(agent_name: str, event_date, event_time):
    print(f"{agent_name} ready at {event_time}")
```

### Available Events
- `AGENT_REGISTERED` - Agent added to orchestrator
- `AGENT_STARTED` - Agent process/thread started
- `AGENT_READY` - Agent completed setup and is ready
- `AGENT_TERMINATED` - Agent stopped execution
- `ORCHESTRATOR_STARTED` - Orchestrator began execution
- `ORCHESTRATOR_STOPPED` - Orchestrator shutdown complete

**Validation:**
- [ ] Event callbacks registered on **Orchestrator**, not agents
- [ ] Callback signatures match event parameters
- [ ] No direct agent-to-agent event handling
- [ ] Events used for monitoring, not control flow

## Dependency Management

### Adding Dependencies
```python
# agent_b starts AFTER agent_a is ready
orchestrator.add_dependency(agent_a_name, agent_b_name)
```

### Dependency Validation
- Circular dependencies are **automatically detected and rejected** at startup
- Dependencies form a directed acyclic graph (DAG)
- Agents start in dependency order

**Validation:**
- [ ] Dependencies declared before `start()`
- [ ] No circular dependency chains
- [ ] All referenced agent names are registered
- [ ] Dependency chains are logical and necessary

### Common Patterns
```python
# Database → API → Worker pattern
orchestrator.register_agent(DatabaseAgent, "db")
orchestrator.register_agent(APIAgent, "api")
orchestrator.register_agent(WorkerAgent, "worker")

orchestrator.add_dependency("db", "api")      # API needs DB
orchestrator.add_dependency("api", "worker")  # Worker needs API
```

## Run Modes

### STOP_ON_EMPTY (Default)
```python
config = Orchestrator.Config(run_mode=RunMode.STOP_ON_EMPTY)
orchestrator = Orchestrator(config=config)
```
- Orchestrator stops when all agents finish
- Best for: Batch processing, finite workflows

### DAEMON
```python
config = Orchestrator.Config(run_mode=RunMode.DAEMON)
orchestrator = Orchestrator(config=config)
```
- Orchestrator keeps running until explicit shutdown
- Best for: Long-running services, continuous processing

**Validation:**
- [ ] Appropriate RunMode for use case
- [ ] DAEMON mode has explicit shutdown mechanism
- [ ] STOP_ON_EMPTY mode handles agent completion properly

## Orchestrator Configuration

### Full Configuration Example
```python
class Config(Orchestrator.Config):
    run_mode: RunMode = RunMode.STOP_ON_EMPTY
    max_startup_time: float = 30.0  # seconds
    shutdown_timeout: float = 10.0   # seconds
    enable_cli: bool = True
    enable_web: bool = False
```

**Validation:**
- [ ] Config inherits from `Orchestrator.Config`
- [ ] Timeouts are reasonable for agent complexity
- [ ] CLI/Web flags match deployment needs

## OMemory (Memory Management)

The Orchestrator uses OMemory to track:
- Agent metadata (AgentEntry objects)
- Agent lifecycle states
- Dependency relationships
- Event history (EventStore)

**Validation:**
- [ ] OMemory used for agent tracking
- [ ] AgentEntry objects properly maintained
- [ ] Memory cleanup on agent termination
- [ ] No memory leaks from long-running orchestrators

## Message Channel Pattern

### Communication Architecture
```
Agent → MessageChannel → Orchestrator → Event System
```

Agents send messages through MessageChannel:
```python
# Inside agent
self.msg_channel.send(message_type, data)
```

Orchestrator receives and dispatches:
```python
# Orchestrator processes messages
# Triggers registered event callbacks
```

**Validation:**
- [ ] All inter-agent communication via Orchestrator
- [ ] No direct agent-to-agent messaging
- [ ] MessageChannel properly initialized
- [ ] Message types handled appropriately

## Lifecycle Management

### Startup Sequence
1. Register all agents
2. Add dependencies
3. Register event callbacks
4. Call `orchestrator.start()`
5. Agents start in dependency order
6. Wait for all agents ready

### Shutdown Sequence
1. Signal shutdown (SIGINT or explicit call)
2. Stop accepting new agent registrations
3. Signal all agents to stop
4. Wait for graceful shutdown (with timeout)
5. Force terminate if timeout exceeded
6. Clean up resources

**Validation:**
- [ ] Proper startup order maintained
- [ ] Graceful shutdown implemented
- [ ] Timeout handling for stuck agents
- [ ] Resource cleanup on exit

## Error Handling

### Agent Failures
- Orchestrator monitors agent termination status
- Events fired for abnormal terminations
- Other agents continue unless dependencies broken

### Orchestrator Failures
- Critical failures propagate to all agents
- Shutdown sequence initiated
- Error logging to orchestrator log

**Validation:**
- [ ] Agent failures don't crash orchestrator
- [ ] Dependency chain failures handled
- [ ] Proper error logging
- [ ] Recovery strategies defined

## Common Anti-Patterns to Avoid

### ❌ DON'T: Direct Agent-to-Agent Communication
```python
# WRONG
agent_a.send_to(agent_b, data)
```

### ✅ DO: Use Orchestrator Events
```python
# CORRECT
# In agent_a
self.msg_channel.send("data_ready", data)

# In orchestrator
orchestrator.register_event("data_ready", handler)
```

### ❌ DON'T: Register Events on Agents
```python
# WRONG
agent.register_event(event_type, callback)
```

### ✅ DO: Register on Orchestrator
```python
# CORRECT
orchestrator.register_event(event_type, callback)
```

### ❌ DON'T: Circular Dependencies
```python
# WRONG - will be rejected
orchestrator.add_dependency("a", "b")
orchestrator.add_dependency("b", "c")
orchestrator.add_dependency("c", "a")  # Circular!
```

### ✅ DO: Linear or Tree Dependencies
```python
# CORRECT
orchestrator.add_dependency("a", "b")
orchestrator.add_dependency("a", "c")
orchestrator.add_dependency("b", "d")
```

### ❌ DON'T: Register After Start
```python
# WRONG
orchestrator.start()
orchestrator.register_agent(LateAgent, "late")  # Too late!
```

### ✅ DO: Register Before Start
```python
# CORRECT
orchestrator.register_agent(Agent1, "a1")
orchestrator.register_agent(Agent2, "a2")
orchestrator.start()  # Now start
```

## Testing Patterns

### Orchestrator Testing
```python
import unittest
from unittest.mock import MagicMock, patch

class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = Orchestrator()
    
    def test_agent_registration(self):
        self.orchestrator.register_agent(TestAgent, "test")
        self.assertIn("test", self.orchestrator.memory.agents)
    
    def test_dependency_validation(self):
        self.orchestrator.register_agent(Agent1, "a1")
        self.orchestrator.register_agent(Agent2, "a2")
        self.orchestrator.add_dependency("a1", "a2")
        # Should not raise
```

**Validation:**
- [ ] Tests cover registration logic
- [ ] Tests verify dependency validation
- [ ] Tests check event system
- [ ] Tests verify lifecycle sequences

## CLI Integration

When `enable_cli=True`:
```bash
# In separate terminal
pyorchestrate ps                    # List agents
pyorchestrate status [agent_name]   # Agent status
pyorchestrate stats                 # Live monitoring
pyorchestrate shutdown              # Graceful shutdown
```

**Validation:**
- [ ] CLI enabled in config if needed
- [ ] CLI commands work as expected
- [ ] CLI doesn't interfere with orchestrator operation

## Reference Examples

Always consult these examples:
- `examples/example_orchestrator_heartbeat.py` - Event system
- `examples/example_agent_callback.py` - Event callbacks
- `examples/example_agent_events.py` - Agent lifecycle events
- `test/test_orchestrator.py` - Orchestrator testing
- `test/test_memory.py` - OMemory testing
