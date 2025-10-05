# PyOrchestrate AI Development Guidelines

## Core Architecture

PyOrchestrate is a **container orchestration framework** for Python processes and threads - think "Docker for Python processes". The key principle is **simplified lifecycle management** where the Orchestrator handles creation, monitoring, and cleanup of isolated execution units (Agents).

### Key Components Hierarchy
```
Orchestrator (process/thread container manager)
├── AgentEntry (container metadata & lifecycle control)
├── BaseAgent (abstract execution unit with Config pattern)
│   ├── PeriodicAgent (scheduled execution: runner() method)
│   ├── LoopingAgent (continuous execution: execute() method)
│   └── PoolAgent (worker pool: runner() with work distribution)
└── Plugin System (inner Plugin class for extensions)
```

## Agent Development Patterns

### 1. Configuration-First Design (Inner Class Pattern)
Every agent **must** follow the Config inner class pattern with type hints:
```python
class MyAgent(PeriodicProcessAgent):
    class Config(PeriodicProcessAgent.Config):
        api_url: str = "https://api.example.com"
        keyword: str = "important"
        execution_interval: float = 5.0  # Required for PeriodicAgent
        limit: int = 10  # Optional: max executions
    
    config: Config  # Type annotation required
```

### 2. Plugin System (Inner Class Pattern)
Use the **Plugin inner class** for extensions - NOT separate registration:
```python
class MyAgent(PeriodicProcessAgent):
    class Plugin(PeriodicProcessAgent.Plugin):
        zmq_pub = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
        zmq_pair = ZeroMQPair("tcp://*:5556", bind=True)
    
    plugin: Plugin  # Type annotation required
    
    def runner(self):
        super().runner()
        # Access plugins directly via self.plugin
        self.plugin.zmq_pub.send(b"Hello")
```

### 3. Lifecycle Methods (ALWAYS call super() FIRST!)
```python
def setup(self):
    super().setup()  # CRITICAL: Call first!
    # Your initialization here
    self.logger.info("Agent initialized")

def runner(self):  # For PeriodicAgent/PoolAgent
    super().runner()  # Handles counters/limits
    # Your business logic

def execute(self):  # For LoopingAgent/BaseAgent
    super().execute()
    # Your business logic

def on_stop(self):
    # Cleanup resources (no super() needed)
    self.logger.info("Cleaning up")
```

### 4. Agent Type Selection
- **PeriodicProcessAgent**: Scheduled tasks, CPU-intensive, isolated memory (uses `runner()`)
- **PeriodicThreadAgent**: Scheduled tasks, I/O-bound, shared memory (uses `runner()`)
- **LoopingProcessAgent**: Continuous loops, CPU-intensive (uses `execute()`)
- **LoopingThreadAgent**: Continuous loops, I/O-bound (uses `execute()`)
- **PoolProcessAgent**: Worker pools for parallel processing (uses `runner()`)

## Development Workflows

### Testing
```bash
# Install dev dependencies first
pip install -r requirements-dev.txt

# Run all tests with verbose output
python3 -m pytest test/ -v --tb=short

# Run specific test file
python3 -m pytest test/test_base_agent.py -v

# Use MagicMock for testing agents (see test/test_base_agent.py)
```

### Code Quality
```bash
# Format code (before commits)
black .

# Lint code
flake8 .
```

### Project Creation
```bash
# Scaffold new project
pyorchestrate create MyApp
# Creates: MyApp/models/, MyApp/configurations/, MyApp/starter.py

# Run orchestrator with CLI enabled
cd MyApp && python starter.py

# CLI commands (in separate terminal)
pyorchestrate ps                    # List agents
pyorchestrate status [agent_name]   # Agent status
pyorchestrate stats                 # Live monitoring (like docker stats)
pyorchestrate shutdown              # Graceful shutdown
```

## Communication & Event Patterns

### Event-Driven Architecture
Agents communicate via **MessageChannel** to Orchestrator - NEVER directly between agents:
```python
# Register callbacks for orchestrator events
orchestrator.register_event(OrchestratorEvent.AGENT_READY, on_agent_ready)
orchestrator.register_event(OrchestratorEvent.AGENT_STARTED, on_agent_started)
orchestrator.register_event(OrchestratorEvent.AGENT_TERMINATED, on_agent_stopped)

def on_agent_ready(agent_name: str, event_date, event_time):
    print(f"{agent_name} ready at {event_time}")
```

### Agent Registration Patterns
```python
orchestrator = Orchestrator()

# Basic registration
orchestrator.register_agent(FileWriter, "FileWriter")

# With custom config
orchestrator.register_agent(
    FileWriter, 
    "FileWriter2",
    custom_config=FileWriter.Config(execution_interval=0.2, directory="/tmp2")
)

# Start and join
orchestrator.start()  # Starts all registered agents
orchestrator.join()   # Wait for completion
```

### Standalone Agent Execution
```python
# Agents can run without Orchestrator
agent = SimpleCounterAgent()
agent.start()

# Wait for lifecycle events
agent.state_events.start_event.wait()   # Agent started
agent.state_events.ready_event.wait()   # Agent ready
agent.state_events.close_event.wait()   # Agent closed
```

## Critical Implementation Details

### Configuration Validation
Override `validate()` in Config classes - return `List[ValidationResult]`:
```python
class Config(PeriodicProcessAgent.Config):
    threshold: int = 10
    validation_policy = ValidationPolicy(ignore_warnings=True, ignore_errors=False)
    
    def validate(self) -> List[ValidationResult]:
        results = super().validate()
        if self.threshold < 0 or self.threshold > 30:
            results.append(ValidationResult(
                field="threshold",
                message="Threshold must be between 0 and 30.",
                severity=ValidationSeverity.ERROR  # Blocks execution
            ))
        return results
```

### Error Handling & Logging
- Use `self.logger` (loguru-based) - never `print()` or `logging`
- Raise `RecoverableException` for retryable errors
- `AgentTerminationStatus` enum: SUCCESS, WARNING, ERROR, CRITICAL
- Each agent gets its own log file in `logs/` directory

### Memory Management & Dependencies
```python
# OMemory tracks agent lifecycle
orchestrator.add_dependency(agent_a, agent_b)  # agent_b starts after agent_a
# Dependencies validated at startup - circular deps rejected
```

### Orchestrator Run Modes
```python
# STOP_ON_EMPTY: Stop when all agents finish (default)
o_config = Orchestrator.Config(run_mode=RunMode.STOP_ON_EMPTY)

# DAEMON: Keep running until explicit shutdown
o_config = Orchestrator.Config(run_mode=RunMode.DAEMON)
orchestrator = Orchestrator(config=o_config)
```

## File Structure & Conventions

- `PyOrchestrate/core/agent/`: Agent base classes (base_agent.py, periodic_agent.py, looping_agent.py, pool_agent.py)
- `PyOrchestrate/core/orchestrator/`: Orchestrator, AgentEntry, OMemory, EventStore
- `PyOrchestrate/core/plugins/`: PluginProtocol, ZeroMQ plugins (com.py), heartbeat plugins
- `PyOrchestrate/core/utilities/`: MessageChannel, events, validation, logging
- `PyOrchestrate/core/base/`: BaseClass, BaseClassConfig, LoggerConfig
- `examples/`: **Reference implementations** - consult these for patterns
- `test/`: Unit tests with MagicMock patterns

## Testing Patterns

Use `unittest.mock.MagicMock` for agent testing (see `test/test_base_agent.py`):
```python
# Mock events and message channel
state_events = BaseAgent.StateEvents(MagicMock(), MagicMock(), MagicMock())
control_events = BaseAgent.ControlEvents(MagicMock(), MagicMock(), MagicMock())
msg_channel = MagicMock()

agent = MyAgent(
    name="test_agent",
    config=config,
    plugin=plugin,
    a_type="process",
    state_events=state_events,
    control_events=control_events,
    msg_channel=msg_channel
)
```

## Version Management

- **CRITICAL**: Update version in BOTH `pyproject.toml` AND `cli.py` (CLIConstants.VERSION)
- CLI entry points: `pyorchestrate` (main CLI), `pyorchestrate-web` (web interface)
- Dependencies: loguru, pyzmq, requests, fastapi, uvicorn, psutil, pydantic (keep minimal)

## Common Patterns (Study examples/)

1. **ALWAYS call `super()` FIRST in setup(), runner(), execute()**
2. **Use type hints**: `config: Config`, `plugin: Plugin`
3. **Plugin inner class**, not manual registration
4. **Access plugins via `self.plugin.plugin_name`**
5. **Event callbacks registered on Orchestrator**, not agents
6. **runner() for Periodic/Pool**, execute() for Looping/Base**
7. **Check `examples/` for patterns** before implementing
8. **Custom attributes via Config `__init__` kwargs**, stored in `_custom_attr`
