# Event System and Lazy Initialization Guide

## Overview

This guide explains the event system and lazy initialization pattern in PyOrchestrate, as recommended in the [Agent Instantiation Report](AGENT_INSTANTIATION_REPORT.md).

---

## Event System

### State Events (Internal State Tracking)

State events track the agent's lifecycle progression:

```
┌──────────────────────────────────────────────────────────┐
│              AGENT STATE EVENTS TIMELINE                 │
└──────────────────────────────────────────────────────────┘

Agent.run() starts
    ↓
state_events.start_event.set()
    ↓ (before setup)
Agent.setup() runs
    ↓
state_events.ready_event.set()
    ↓ (after setup, before execution)
Agent.execute() runs
    ↓
    (User code execution)
    ↓
state_events.close_event.set()
    ↓ (in finally block, during cleanup)
Agent terminates
```

#### Using State Events

**Synchronization Pattern:**

```python
# Start agent
agent = MyAgent(name="test")
agent.start()

# Wait for specific state
if agent.state_events.start_event.wait(timeout=5):
    print("Agent started successfully")
else:
    print("Agent startup timeout")

if agent.state_events.ready_event.wait(timeout=5):
    print("Agent ready for work")
else:
    print("Agent setup timeout")

if agent.state_events.close_event.wait(timeout=30):
    print("Agent completed")
else:
    print("Agent execution timeout")
```

### Control Events (External Flow Control)

Control events allow external code to control agent execution:

```
┌──────────────────────────────────────────────────────────┐
│            AGENT CONTROL EVENTS TIMELINE                 │
└──────────────────────────────────────────────────────────┘

Agent.run() starts
    ↓
control_events.setup_event.wait()
    ↓ (blocks here if setup_event is not set)
Agent.setup() runs (only if setup_event is set)
    ↓
control_events.execute_event.wait()
    ↓ (blocks here if execute_event is not set)
Agent.execute() runs (only if execute_event is set)
    ↓
    (Check control_events.stop_event in loop)
    ↓
control_events.stop_event.is_set() = True
    ↓
Agent terminates
```

#### Default Control Event Behavior

By default, control events are **pre-set to ready**:

```python
# In BaseAgent.__init__
if not control_events:
    # Auto-created events are set to ready
    self.control_events.setup_event.set()
    self.control_events.execute_event.set()
    # stop_event is NOT set (stays in "not stopped" state)
```

#### Using Control Events for Paused Execution

**Scenario: Delay Setup Until External Signal**

```python
# Create control events that are NOT set
setup_event = threading.Event()      # Not set = will block
execute_event = threading.Event()    # Not set = will block
stop_event = threading.Event()

custom_control = BaseAgent.ControlEvents(
    setup_event=setup_event,
    execute_event=execute_event,
    stop_event=stop_event
)

# Create agent with paused execution
agent = MyAgent(
    name="paused_agent",
    control_events=custom_control
)

# Start agent (but it will block in setup)
agent.start()
print("Agent started but waiting for setup_event...")

# Later, when ready to proceed
input("Press Enter to allow setup...")
setup_event.set()

# Now agent can proceed to execution, but will block again
input("Press Enter to allow execution...")
execute_event.set()

# Now agent executes normally
```

#### Using Control Events for Graceful Shutdown

```python
class MyAgent(LoopingThreadAgent):
    def execute(self):
        super().execute()
        
        while True:
            # Check if stop was requested
            if self.control_events.stop_event.is_set():
                self.logger.info("Stop requested, exiting")
                break
            
            # Do work
            self.logger.info("Processing...")
            time.sleep(1)

# Usage
agent = MyAgent(name="graceful_agent")
agent.start()

# Let it run for a bit
time.sleep(5)

# Request graceful shutdown
agent.stop()  # Sets stop_event
agent.state_events.close_event.wait()  # Wait for completion
```

---

## Lazy Initialization Pattern

### What is Lazy Initialization?

Lazy initialization means deferring object creation until it's actually needed. In PyOrchestrate:

```
Registration Phase (Synchronous)
    ↓
    User calls: orchestrator.register_agent(MyAgent, "agent1", ...)
    ↓
    Orchestrator stores METADATA only (not the actual agent instance)
    ↓
    Very fast - no object creation
    
Initialization Phase (On Start)
    ↓
    User calls: orchestrator.start()
    ↓
    For each registered agent:
        - Orchestrator calls AgentEntry.initialize_agent()
        - Agent instance is CREATED here (expensive operation)
        - Then Agent.start() is called (process/thread starts)
```

### Benefits of Lazy Initialization

1. **Memory Efficiency**: Agents only exist when needed
2. **Fast Startup**: Registration is quick, only initialization takes time
3. **Flexible Event Setup**: Events can be created with correct type at right time
4. **Better Error Handling**: Errors happen at start time, not registration time

### How It Works in Code

```python
# Phase 1: Registration (Synchronous)
entry = orchestrator.register_agent(
    MyAgent, 
    "my_agent",
    custom_config=MyAgent.Config(param="value"),
    custom_plugin=MyAgent.Plugin()
)
# At this point: entry._instance is None (not created yet)
print(entry._instance)  # Output: None

# Phase 2: Initialization (When starting)
entry.initialize_agent()  # Creates the actual agent instance
# At this point: entry._instance is a MyAgent object
print(entry._instance)  # Output: <MyAgent object>
```

### Parameter Propagation in Lazy Initialization

```
User provides parameters
    ↓
Orchestrator.register_agent() stores in AgentEntry
    ├── config → AgentEntry.config
    ├── plugin → AgentEntry.plugin
    ├── control_events → AgentEntry.control_events
    ├── state_events → AgentEntry.state_events
    └── msg_channel → AgentEntry.kwargs["msg_channel"]
    
During AgentEntry.initialize_agent():
    ↓
    Build parameters dict from stored values
    ↓
    Pass to Agent.__init__()
    ↓
    Agent stores them as instance attributes
    ├── agent.config (from parameter or default)
    ├── agent.plugin (from parameter or default)
    ├── agent.control_events (from parameter or auto-created)
    ├── agent.state_events (from parameter or auto-created)
    └── agent.msg_channel (from parameter or default)
```

---

## Error Handling During Lifecycle

### Validation Error Handling

If configuration validation fails during setup:

```python
try:
    self.validate_config()  # In Agent.run()
except ConfigValidationError as e:
    self.logger.error(f"Agent cannot start due to configuration error.")
    self.termination_status = AgentTerminationStatus.ERROR
    # Continues to finally block (cleanup)
```

**Outcome:**
- Agent does NOT proceed to execute phase
- Cleanup (on_close) still executes
- close_event is still set
- Error is logged to agent-specific log file

### Execution Error Handling

If an error occurs during execute():

```python
except Exception as ex:
    self.logger.exception(f"Error during execution: {ex}")
    self.termination_status = AgentTerminationStatus.CRITICAL
    
    # Send error message to orchestrator
    error_message = ServiceMessage.create_status(
        sender=self.name,
        status="error",
        error=str(ex),
    )
    self.send_message(error_message)
    # Continues to finally block (cleanup)
```

**Outcome:**
- Error is logged with full traceback
- Orchestrator is notified via message
- Cleanup (on_close) still executes
- close_event is still set
- termination_status is CRITICAL

### Cleanup Always Executes (Finally Block)

```python
finally:
    self.on_close()                      # User cleanup
    self.plugin_manager.finalize_plugins()  # Plugin cleanup
    self._handle_stop()                  # Send AGENT_CLOSE message
    if self.state_events is not None:
        self.state_events.close_event.set()
    
    elapsed = time.time() - self.start_time
    self.logger.debug(f"Agent completed in {elapsed:.3f}s with status: {self.termination_status.value}")
```

This ensures:
- Resources are always released
- Orchestrator is always notified
- close_event is always set
- Logs always contain completion info

---

## Best Practices

### 1. Always Call super() First

```python
def setup(self):
    super().setup()  # MUST be first
    # Your setup code here

def execute(self):
    super().execute()  # MUST be first
    # Your execution code here

def on_close(self):
    # No super() needed here
    # Your cleanup code here
```

### 2. Handle Cleanup Errors Gracefully

```python
def on_close(self):
    try:
        self.logger.info("Closing connections")
        if hasattr(self, 'connection'):
            self.connection.close()
    except Exception as e:
        # Log but don't re-raise
        self.logger.error(f"Error during cleanup: {e}")
```

### 3. Check Stop Event in Loops

```python
def execute(self):
    super().execute()
    while not self.control_events.stop_event.is_set():
        # Do work
        self.logger.info("Working...")
        time.sleep(1)
```

### 4. Use State Events for Synchronization

```python
# External code waiting for agent readiness
if agent.state_events.ready_event.wait(timeout=10):
    print("Agent ready, starting tasks")
    # Safe to use agent now
else:
    print("Agent setup took too long")
```

### 5. Document Config Requirements

```python
class MyAgent(PeriodicProcessAgent):
    class Config(PeriodicProcessAgent.Config):
        api_key: str  # REQUIRED - API key for service
        api_url: str = "https://api.example.com"  # Has default
        timeout: float = 30.0  # Optional with default
    
    def validate_config(self):
        # Check required fields
        if not self.config.api_key:
            raise ConfigValidationError("api_key is required")
```

---

## Common Issues and Solutions

### Issue: Agent Hangs During Setup

**Cause:** setup_event is not set

**Solution:**

```python
# Don't create paused setup_event unless you intend to
control_events = BaseAgent.ControlEvents(
    setup_event=threading.Event(),  # Not set = blocks
    ...
)
# Instead, either:
# 1. Don't provide control_events (auto-created, pre-set)
# 2. Set the event after creation
```

### Issue: Agent Doesn't Stop

**Cause:** execute() doesn't check stop_event

**Solution:**

```python
def execute(self):
    super().execute()
    
    # Check stop_event in loop
    while not self.control_events.stop_event.is_set():
        self.logger.info("Working")
        time.sleep(1)
    
    self.logger.info("Stop requested, exiting gracefully")
```

### Issue: Resources Not Released

**Cause:** on_close() not implemented or raises exception

**Solution:**

```python
def on_close(self):
    try:
        # Clean up resources
        if hasattr(self, 'file'):
            self.file.close()
        if hasattr(self, 'connection'):
            self.connection.close()
    except Exception as e:
        self.logger.error(f"Cleanup error: {e}")
        # Don't re-raise - must complete cleanup
```

---

## References

- [Agent Instantiation Report](AGENT_INSTANTIATION_REPORT.md)
- [PyOrchestrate Core Architecture](./index.md)
- Source: `PyOrchestrate/core/agent/base_agent.py`
- Source: `PyOrchestrate/core/orchestrator/memory.py`

---

**Last Updated:** 2025-11-15
**Status:** Final
