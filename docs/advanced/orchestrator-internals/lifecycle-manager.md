---
title: AgentLifecycleManager
editLink: true
---

# AgentLifecycleManager

The **AgentLifecycleManager** manages the complete lifecycle of agents, from registration through termination. It handles all aspects of creating, configuring, starting, and stopping agents within the orchestrator.

## Purpose and Design

Agents don't exist in isolation—they need to be registered, configured, instantiated as processes or threads, and gracefully shut down when done. The AgentLifecycleManager centralizes all these responsibilities into a single, cohesive component.

## Core Responsibilities

| Responsibility | Description |
|---------------|-------------|
| **Agent Registration** | Register agents with configurations and plugins |
| **Instance Creation** | Create agent processes/threads with proper wiring |
| **Event Wiring** | Connect agents to orchestrator event system |
| **Message Channel Injection** | Enable agent-orchestrator communication |
| **Graceful Shutdown** | Cleanly stop all agents with timeout handling |

## Agent Registration

### Basic Registration

Register an agent with the orchestrator:

```python
orchestrator.register_agent(
    agent_class=MyAgent,
    name="worker1"
)
```

### Registration with Custom Configuration

Provide agent-specific configuration:

```python
orchestrator.register_agent(
    DataProcessor,
    "processor1",
    custom_config=DataProcessor.Config(
        batch_size=100,
        timeout=30.0
    )
)
```

### Registration with Custom Plugins

Override default plugins:

```python
custom_plugins = DataProcessor.Plugins()
custom_plugins.communication = ZeroMQPubSubPlugin(...)

orchestrator.register_agent(
    DataProcessor,
    "processor2",
    custom_plugins=custom_plugins
)
```

## Agent Entry Structure

Each registered agent is stored as an `AgentEntry` containing:

| Field | Purpose |
|-------|---------|
| `name` | Unique agent identifier |
| `agent_class` | Agent class reference for instantiation |
| `custom_config` | Optional custom configuration |
| `custom_plugins` | Optional custom plugin overrides |
| `state_events` | Lifecycle events (started, ready, terminated, error) |
| `control_events` | Control signals (pause, resume, stop, shutdown) |
| `process`/`thread` | Handle to the running agent instance |

## Agent Instantiation

## Agent Instantiation

### Process vs Thread Mode

The lifecycle manager can create agents as either **processes** or **threads** based on orchestrator configuration:

| Mode | Use Case | Isolation | Communication |
|------|----------|-----------|---------------|
| **Process** | CPU-intensive work, isolation needed | Full memory isolation | Inter-process MessageChannel |
| **Thread** | I/O-intensive work, shared memory | Shared memory space | Direct memory access |

```python
# Configure execution mode
config = OrchestratorConfig(use_multiprocessing=True)  # Processes
config = OrchestratorConfig(use_multiprocessing=False) # Threads
```

### Agent Lifecycle Flow

When an agent starts, the lifecycle manager:

1. **Instantiates** the agent class with provided configuration
2. **Wires events** (StateEvents for monitoring, ControlEvents for control)
3. **Injects MessageChannel** for orchestrator communication
4. **Applies custom plugins** if provided
5. **Initializes** the agent (calls `initialize()`)
6. **Runs** the agent (calls `run()`)
7. **Finalizes** on termination (calls `finalize()`)

## Event Wiring

### StateEvents: Monitoring Agent Lifecycle

StateEvents allow the orchestrator to monitor what's happening with agents:

| Event | When Set | Purpose |
|-------|----------|---------|
| `started` | Agent begins execution | Know when agent is up |
| `ready` | Agent signals readiness | Know when agent can work |
| `terminated` | Agent completes or stops | Know when agent is done |
| `error` | Agent encounters error | Know when something went wrong |

**Example**: Waiting for agent readiness

```python
agent_entry = orchestrator.memory.agents["worker1"]

if agent_entry.state_events.ready.wait(timeout=10.0):
    print("Agent is ready to work")
else:
    print("Agent startup timeout")
```

### ControlEvents: Controlling Agent Execution

ControlEvents allow the orchestrator to send signals to agents:

| Event | Purpose | Agent Response |
|-------|---------|----------------|
| `pause` | Temporarily pause agent | Stop processing but stay alive |
| `resume` | Resume paused agent | Continue processing |
| `stop` | Graceful shutdown | Complete current work and exit |
| `shutdown` | Force termination | Exit immediately |

**Example**: Pausing and resuming an agent

```python
agent_entry = orchestrator.memory.agents["worker1"]

# Pause agent
agent_entry.control_events.pause.set()
time.sleep(5)

# Resume agent
agent_entry.control_events.resume.set()
```

## Message Channel Integration

The lifecycle manager injects the orchestrator's `MessageChannel` into each agent, enabling bidirectional communication:

```
Agent Process/Thread
    ↓ sends status updates via MessageChannel
Orchestrator (MessageRouter)
    ↓ translates to OrchestratorEvents
OrchestratorEventBus
    ├─→ Execute callbacks
    └─→ Record to history
```

Agents automatically send lifecycle messages:
- Agent started → `AgentEvent.AGENT_STARTED`
- Agent ready → `AgentEvent.AGENT_READY`
- Agent error → `AgentEvent.AGENT_ERROR`
- Agent terminated → `AgentEvent.AGENT_TERMINATED`

These are received by the `MessageRouter` and converted to orchestrator events.

## Graceful Shutdown

### Stop All Agents

The lifecycle manager can gracefully stop all registered agents:

```python
# Stop all agents with 30 second timeout
orchestrator.lifecycle_manager.stop_all(timeout=30.0)
```

**What happens**:
1. `stop` control event is set for all agents
2. Manager waits up to `timeout` seconds for each agent
3. If agent doesn't stop in time, it's forcefully terminated
4. Resources are cleaned up

### Individual Agent Shutdown

Stop a specific agent:

```python
orchestrator.lifecycle_manager.stop_agent("worker1", timeout=10.0)
```

## Integration with PluginManager

The lifecycle manager coordinates with the `PluginManager` to handle agent plugins:

**During agent startup**:
1. Agent instance is created
2. Plugins are initialized via `plugin_manager.initialize_plugins()`
3. Agent runs with initialized plugins

**During agent shutdown**:
1. Agent completes execution
2. Plugins are finalized via `plugin_manager.finalize_plugins()`
3. Resources are cleaned up

This ensures plugins have proper initialization and cleanup lifecycle.

## Error Handling

### Agent Initialization Failures

If an agent fails to start, the lifecycle manager:
- Logs the error
- Marks the agent entry as failed
- Allows retry or removal
- Doesn't affect other agents

### Runtime Agent Failures

Agents communicate failures via StateEvents:

```python
agent_entry = orchestrator.memory.agents["worker1"]

if agent_entry.state_events.error.is_set():
    logger.error(f"Agent {agent_entry.name} encountered error")
    
    # Options:
    # 1. Restart agent
    orchestrator.lifecycle_manager.stop_agent("worker1")
    orchestrator.lifecycle_manager.start_agent("worker1")
    
    # 2. Remove from system
    del orchestrator.memory.agents["worker1"]
```

## Common Use Cases

### Dynamic Agent Registration

Add agents dynamically during runtime:

```python
# Start orchestrator with initial agents
orchestrator.start()

# Later, add more agents on-demand
for i in range(10):
    orchestrator.register_agent(WorkerAgent, f"dynamic_worker_{i}")
    orchestrator.lifecycle_manager.start_agent(f"dynamic_worker_{i}")
```

### Agent Pools

Create pools of identical workers:

```python
for i in range(num_workers):
    orchestrator.register_agent(
        WorkerAgent,
        f"worker_{i}",
        custom_config=WorkerAgent.Config(
            worker_id=i,
            task_queue=shared_queue
        )
    )
```

### Conditional Agent Starting

Start agents based on configuration:

```python
if config.enable_monitoring:
    orchestrator.register_agent(MonitorAgent, "monitor")

if config.enable_cache:
    orchestrator.register_agent(CacheAgent, "cache")

orchestrator.start()  # Starts only enabled agents
```

## Best Practices

### 1. Use Unique, Descriptive Agent Names

```python
# ✅ Good: Descriptive names
orchestrator.register_agent(DataCollector, "data_collector_prod")
orchestrator.register_agent(DataProcessor, "data_processor_batch")

# ❌ Bad: Generic names
orchestrator.register_agent(DataCollector, "agent1")
```

### 2. Validate Configuration Before Registration

```python
try:
    config = MyAgent.Config(interval=5.0)
    config._validate()
    orchestrator.register_agent(MyAgent, "agent", custom_config=config)
except ConfigValidationError as e:
    logger.error(f"Invalid config: {e}")
```

### 3. Allow Time for Graceful Shutdown

```python
try:
    orchestrator.lifecycle_manager.stop_all(timeout=30.0)
except Exception as e:
    logger.error(f"Shutdown error: {e}")
finally:
    orchestrator.finalize()
```

### 4. Monitor Agent State

```python
# Check agent health periodically
for agent_name, agent_entry in orchestrator.memory.agents.items():
    if agent_entry.state_events.error.is_set():
        logger.warning(f"Agent {agent_name} in error state")
```

## See Also

- [DependencyGraph](./dependency-graph.md) - Determines agent startup order
- [WorkerPoolScheduler](./worker-pool.md) - Manages concurrent agent execution
- [PluginManager](../../learn/utilities/plugin-manager.md) - Plugin lifecycle management
- [MessageChannel](../../learn/utilities/message-channel.md) - Inter-agent communication
- [Orchestrator Internals](./index.md) - Architecture overview

### Agent Runner

The agent runner is responsible for instantiating and running the agent:

```python
def _agent_runner(self, agent_name: str):
    """
    Runner function executed in agent's process/thread.
    
    Handles:
    - Agent instantiation
    - Event wiring (StateEvents, ControlEvents)
    - MessageChannel injection
    - Agent lifecycle (initialize, run, finalize)
    - Error handling and logging
    """
    try:
        agent_entry = self.memory.agents[agent_name]
        
        # Instantiate agent
        agent_instance = agent_entry.agent_class(
            config=agent_entry.custom_config or agent_entry.agent_class.Config()
        )
        
        # Wire events
        agent_instance.state_events = agent_entry.state_events
        agent_instance.control_events = agent_entry.control_events
        
        # Inject message channel for orchestrator communication
        agent_instance.message_channel = self.message_channel
        
        # Override plugins if custom provided
        if agent_entry.custom_plugins:
            agent_instance.plugins = agent_entry.custom_plugins
        
        # Initialize and run
        agent_instance.initialize()
        agent_instance.run()
        
    except Exception as e:
        self.logger.error(f"Agent {agent_name} failed: {e}")
        raise
    finally:
        # Cleanup
        try:
            agent_instance.finalize()
        except:
            pass
```

## Event Wiring

### StateEvents

StateEvents allow the orchestrator to monitor agent lifecycle:

```python
@dataclass
class StateEvents:
    started: Event       # Set when agent starts
    ready: Event         # Set when agent is ready
    terminated: Event    # Set when agent terminates
    error: Event         # Set on agent error
```

### ControlEvents

ControlEvents allow the orchestrator to control agents:

```python
@dataclass
class ControlEvents:
    pause: Event         # Pause agent execution
    resume: Event        # Resume agent execution
    stop: Event          # Stop agent gracefully
    shutdown: Event      # Force shutdown
```

### Event Usage

```python
# Orchestrator monitors agent state
agent_entry = orchestrator.memory.agents["worker1"]

# Wait for agent to be ready
if agent_entry.state_events.ready.wait(timeout=10.0):
    print("Agent is ready")
else:
    print("Agent startup timeout")

# Control agent execution
agent_entry.control_events.pause.set()  # Pause agent
time.sleep(5)
agent_entry.control_events.resume.set()  # Resume agent
```

## Message Channel Integration

The lifecycle manager injects the orchestrator's `MessageChannel` into each agent:

```python
# In agent_runner
agent_instance.message_channel = self.message_channel

# Agent can now send messages to orchestrator
class MyAgent(BaseAgent):
    def _handle_ready(self):
        # Send ready notification to orchestrator
        self.send_message(ServiceMessage.create_status(
            sender=self.name,
            status="ready",
            event_name=AgentEvent.AGENT_READY.value
        ))
```

The MessageRouter then receives these messages and converts them to orchestrator events.

## Graceful Shutdown

### Stop All Agents

```python
def stop_all(self, timeout: float = 10.0):
    """
    Stop all registered agents gracefully.
    
    Args:
        timeout: Maximum time to wait for each agent to stop
    """
    for agent_name, agent_entry in self.memory.agents.items():
        try:
            # Signal agent to stop
            agent_entry.control_events.stop.set()
            
            # Wait for termination
            if agent_entry.process:
                agent_entry.process.join(timeout)
                if agent_entry.process.is_alive():
                    self.logger.warning(f"Force terminating {agent_name}")
                    agent_entry.process.terminate()
            
            elif agent_entry.thread:
                agent_entry.thread.join(timeout)
                if agent_entry.thread.is_alive():
                    self.logger.warning(f"Thread {agent_name} did not stop")
        
        except Exception as e:
            self.logger.error(f"Error stopping {agent_name}: {e}")
```

### Individual Agent Stop

```python
def stop_agent(self, agent_name: str, timeout: float = 10.0):
    """
    Stop a specific agent gracefully.
    
    Args:
        agent_name: Name of agent to stop
        timeout: Maximum time to wait for stop
    """
    if agent_name not in self.memory.agents:
        raise ValueError(f"Agent '{agent_name}' not registered")
    
    agent_entry = self.memory.agents[agent_name]
    agent_entry.control_events.stop.set()
    
    # Wait for graceful termination
    if not agent_entry.state_events.terminated.wait(timeout):
        self.logger.warning(f"Agent {agent_name} did not terminate, forcing...")
        if agent_entry.process:
            agent_entry.process.terminate()
```

## Integration with PluginManager

The lifecycle manager works with the PluginManager to handle plugin initialization:

```python
# During agent registration
agent_entry = AgentEntry(...)

# Plugin manager is created for each agent
agent_instance.plugin_manager = PluginManager(agent_instance.plugins)
agent_instance.plugin_manager.set_owner(agent_instance)

# Plugins are initialized before agent runs
agent_instance.plugin_manager.initialize_plugins()

# Agent runs with initialized plugins
agent_instance.run()

# Plugins are finalized on agent termination
agent_instance.plugin_manager.finalize_plugins()
```

## Error Handling

### Agent Initialization Failures

```python
try:
    lifecycle_manager.start_agent("worker1")
except Exception as e:
    logger.error(f"Failed to start agent: {e}")
    # Agent entry remains registered but not started
    # Can retry or remove from registry
```

### Runtime Agent Failures

```python
# Agent failures are communicated via StateEvents
agent_entry = memory.agents["worker1"]

if agent_entry.state_events.error.wait(timeout=1.0):
    logger.error(f"Agent {agent_entry.name} encountered error")
    
    # Orchestrator can take action:
    # 1. Restart agent
    lifecycle_manager.stop_agent("worker1")
    lifecycle_manager.start_agent("worker1")
    
    # 2. Or remove from system
    # del memory.agents["worker1"]
```

## Common Use Cases

### Dynamic Agent Registration

```python
# Add agents dynamically during orchestrator runtime
orchestrator.register_agent(WorkerAgent, f"worker_{i}")
orchestrator.start()  # Only starts previously registered agents

# Later, add more agents
for i in range(10):
    orchestrator.register_agent(WorkerAgent, f"dynamic_worker_{i}")
    orchestrator.lifecycle_manager.start_agent(f"dynamic_worker_{i}")
```

### Agent Pools

```python
# Create pool of identical workers
for i in range(num_workers):
    orchestrator.register_agent(
        WorkerAgent,
        f"worker_{i}",
        custom_config=WorkerAgent.Config(
            worker_id=i,
            task_queue=shared_queue
        )
    )
```

### Conditional Agent Starting

```python
# Start agents based on configuration
if config.enable_monitoring:
    orchestrator.register_agent(MonitorAgent, "monitor")

if config.enable_cache:
    orchestrator.register_agent(CacheAgent, "cache")

orchestrator.start()  # Starts only enabled agents
```

## Testing

Example unit test for AgentLifecycleManager:

```python
import unittest
from unittest.mock import Mock, patch
from PyOrchestrate.core.orchestrator.lifecycle_manager import AgentLifecycleManager

class TestAgentLifecycleManager(unittest.TestCase):
    def setUp(self):
        self.memory = Mock()
        self.memory.agents = {}
        self.manager = AgentLifecycleManager(
            memory=self.memory,
            config=Mock(),
            message_channel=Mock(),
            logger=Mock()
        )
    
    def test_register_agent(self):
        """Test agent registration"""
        agent_entry = self.manager.register_agent(
            agent_class=MockAgent,
            name="test_agent"
        )
        
        self.assertEqual(agent_entry.name, "test_agent")
        self.assertIn("test_agent", self.memory.agents)
    
    def test_duplicate_registration_fails(self):
        """Test that duplicate names are rejected"""
        self.manager.register_agent(MockAgent, "test_agent")
        
        with self.assertRaises(ValueError):
            self.manager.register_agent(MockAgent, "test_agent")
```

## Best Practices

### 1. Unique Agent Names

```python
# Good: Unique, descriptive names
orchestrator.register_agent(DataCollector, "data_collector_prod")
orchestrator.register_agent(DataProcessor, "data_processor_batch")

# Bad: Generic or duplicate names
orchestrator.register_agent(DataCollector, "agent1")  # ❌ Not descriptive
orchestrator.register_agent(DataProcessor, "agent1")  # ❌ Duplicate
```

### 2. Configuration Validation

```python
# Validate configuration before registration
try:
    config = MyAgent.Config(interval=5.0)
    config._validate()
    orchestrator.register_agent(MyAgent, "agent", custom_config=config)
except ConfigValidationError as e:
    logger.error(f"Invalid config: {e}")
```

### 3. Graceful Shutdown

```python
# Always allow time for graceful shutdown
try:
    orchestrator.lifecycle_manager.stop_all(timeout=30.0)
except Exception as e:
    logger.error(f"Shutdown error: {e}")
finally:
    # Ensure resources are cleaned up
    orchestrator.finalize()
```

## See Also

- [DependencyGraph](./dependency-graph.md) - Determines agent startup order
- [WorkerPoolScheduler](./worker-pool.md) - Manages concurrent agent execution
- [PluginManager](../../learn/utilities/plugin-manager.md) - Plugin lifecycle management
- [MessageChannel](../../learn/utilities/message-channel.md) - Inter-agent communication
