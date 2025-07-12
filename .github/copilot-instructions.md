# PyOrchestrate AI Development Guidelines

## Core Architecture

PyOrchestrate is a **container orchestration framework** for Python processes and threads - think "Docker for Python processes". The key principle is **simplified lifecycle management** where the Orchestrator handles creation, monitoring, and cleanup of isolated execution units (Agents).

### Key Components Hierarchy
```
Orchestrator (process/thread container manager)
├── AgentEntry (container metadata & lifecycle)
├── BaseAgent (abstract execution unit with Config pattern)
│   ├── PeriodicAgent (scheduled execution containers)
│   ├── LoopingAgent (continuous execution containers)
│   └── PoolAgent (worker pool containers)
└── Plugin System (inter-container communication)
```

## Agent Development Patterns

### 1. Configuration-First Design
Every agent follows the **Config inner class pattern**:
```python
class MyAgent(PeriodicProcessAgent):
    class Config(PeriodicProcessAgent.Config):
        api_url: str = "https://api.example.com"
        keyword: str = "important"
        execution_interval: float = 5.0
    
    config: Config
```

### 2. Lifecycle Methods (Call super() first!)
- `setup()`: Initialize resources, plugins, connections
- `execute()` or `runner()`: Core business logic
- `on_stop()`: Cleanup resources

### 3. Process vs Thread Agents
- Use `*ProcessAgent` for CPU-intensive, isolated tasks
- Use `*ThreadAgent` for I/O-bound, shared-memory tasks
- Pattern: `BaseAgent` → `PeriodicAgent` → `PeriodicProcessAgent`

## Development Workflows

### Testing
```bash
# Install dev dependencies first
pip install -r requirements-dev.txt
python3 -m pytest test/ -v --tb=short
```

### Code Quality
```bash
# Format code
black .
# Lint code  
flake8 .
```

### Project Creation
```bash
# Use CLI to scaffold new projects
pyorchestrate start MyApp
# Creates: models/, configurations/, starter.py
```

## Communication Patterns

### Event-Driven Architecture
- Agents communicate via **MessageChannel** to Orchestrator
- Orchestrator handles ALL event processing centrally
- Use `AgentEvent` for state changes, `OrchestratorEvent` for control

### Plugin System
Register plugins in `setup()`:
```python
def setup(self):
    super().setup()
    self.register_plugin(ZeroMQPlugin("tcp://localhost:5555", zmq.PUB))
    self.register_plugin(HTTPPlugin("http://localhost:8000"))
```

## Critical Implementation Details

### Memory Management
- `OMemory` class tracks agent lifecycle and dependencies
- Agent dependencies validated before startup
- Use `orchestrator.add_dependency(agent_a, agent_b)` for ordering

### Configuration Validation
- Override `validate()` in Config classes
- Return `List[ValidationResult]` with severity levels
- Framework enforces validation policies automatically

### Error Handling
- `AgentTerminationStatus` enum for exit states
- Use structured logging via `self.logger` (loguru-based)
- Validation errors raise `ConfigValidationError`

## File Structure Conventions

- `PyOrchestrate/core/agent/`: Agent base classes
- `PyOrchestrate/core/orchestrator/`: Orchestration logic
- `PyOrchestrate/core/plugins/`: Extension system
- `examples/`: Reference implementations (study these!)
- `test/`: Unit tests with mocking patterns

## Version & Release Management

- Update version in `pyproject.toml` and `cli.py` synchronously
- CLI uses `pyorchestrate` entry point
- Documentation auto-generated with mkdocs + mkdocstrings
- Dependencies: loguru, pyzmq, requests (keep minimal)

## Common Patterns to Follow

1. **Always call `super()` in lifecycle methods**
2. **Use type hints extensively** (`config: Config`)
3. **Follow the Config inner class pattern** for all agents
4. **Register plugins in setup()**, not __init__
5. **Use examples/ as reference** for implementation patterns
6. **Centralize event handling** through Orchestrator, not direct agent communication
