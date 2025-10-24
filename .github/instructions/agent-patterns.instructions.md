---
applyTo: "PyOrchestrate/core/agent/**/*.py"
description: "Agent development patterns and requirements for PyOrchestrate"
---

# Agent Development Pattern Rules

## Critical Requirements

### 1. Configuration Inner Class Pattern
Every agent **MUST** have an inner Config class:
```python
class MyAgent(PeriodicProcessAgent):
    class Config(PeriodicProcessAgent.Config):
        # Required fields with type hints
        execution_interval: float = 5.0  # For PeriodicAgent
        custom_field: str = "value"
    
    config: Config  # Type annotation REQUIRED
```

**Validation:**
- [ ] Inner `Config` class exists
- [ ] Inherits from parent agent's Config
- [ ] Has type hints for all fields
- [ ] Agent has `config: Config` type annotation

### 2. Plugin Inner Class Pattern
If using plugins, use inner Plugin class:
```python
class MyAgent(PeriodicProcessAgent):
    class Plugin(PeriodicProcessAgent.Plugin):
        zmq_pub = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
    
    plugin: Plugin  # Type annotation REQUIRED
```

**Validation:**
- [ ] Inner `Plugin` class (NOT manual registration)
- [ ] Inherits from parent agent's Plugin
- [ ] Agent has `plugin: Plugin` type annotation
- [ ] Access via `self.plugin.plugin_name`

### 3. Lifecycle Method Super() Calls
**ALWAYS call super() FIRST** in lifecycle methods:

```python
def setup(self):
    super().setup()  # MUST be first line!
    # Your initialization

def runner(self):  # For PeriodicAgent/PoolAgent
    super().runner()  # MUST be first line!
    # Your logic

def execute(self):  # For LoopingAgent/BaseAgent
    super().execute()  # MUST be first line!
    # Your logic

def on_stop(self):
    # Cleanup - no super() needed
    pass
```

**Validation:**
- [ ] `super().setup()` is first line in `setup()`
- [ ] `super().runner()` is first line in `runner()` (if exists)
- [ ] `super().execute()` is first line in `execute()` (if exists)

### 4. Method Name Selection
Choose correct method based on agent type:

- **PeriodicAgent** → Use `runner()` (scheduled execution)
- **LoopingAgent** → Use `execute()` (continuous loop)
- **PoolAgent** → Use `runner()` (worker distribution)
- **BaseAgent** → Use `execute()` (custom control)

**Validation:**
- [ ] Correct method name for agent type
- [ ] No mixing of `runner()` and `execute()` in same agent

## Agent Type Selection

### PeriodicProcessAgent
- **Use for**: CPU-intensive scheduled tasks
- **Characteristics**: Isolated memory, scheduled execution
- **Method**: `runner()`
- **Required Config**: `execution_interval: float`

### PeriodicThreadAgent
- **Use for**: I/O-bound scheduled tasks
- **Characteristics**: Shared memory, scheduled execution
- **Method**: `runner()`
- **Required Config**: `execution_interval: float`

### LoopingProcessAgent
- **Use for**: CPU-intensive continuous tasks
- **Characteristics**: Isolated memory, continuous loop
- **Method**: `execute()`

### LoopingThreadAgent
- **Use for**: I/O-bound continuous tasks
- **Characteristics**: Shared memory, continuous loop
- **Method**: `execute()`

### PoolProcessAgent
- **Use for**: Parallel processing with worker pools
- **Characteristics**: Multiple workers, work distribution
- **Method**: `runner()`
- **Required Config**: `pool_size: int`, `execution_interval: float`

## Logging Requirements

**ALWAYS use `self.logger`, NEVER `print()` or `logging` module:**

```python
self.logger.info("Agent started")
self.logger.warning("Potential issue detected")
self.logger.error("Error occurred", error=str(e))
self.logger.debug("Debug information")
```

**Validation:**
- [ ] Uses `self.logger` for all logging
- [ ] No `print()` statements
- [ ] No direct `logging` module usage

## Error Handling

### Recoverable Exceptions
Use `RecoverableException` for retryable errors:
```python
from PyOrchestrate.core.base.exceptions import RecoverableException

try:
    # operation
except SomeError as e:
    raise RecoverableException(f"Temporary failure: {e}")
```

### Termination Status
Set appropriate termination status in `on_stop()`:
```python
from PyOrchestrate.core.utilities import AgentTerminationStatus

def on_stop(self):
    if self.error_occurred:
        self.termination_status = AgentTerminationStatus.ERROR
    else:
        self.termination_status = AgentTerminationStatus.SUCCESS
```

**Validation:**
- [ ] Uses `RecoverableException` for retryable errors
- [ ] Sets appropriate `AgentTerminationStatus`
- [ ] Proper exception handling in critical sections

## Configuration Validation

Implement custom validation in Config class:
```python
class Config(PeriodicProcessAgent.Config):
    threshold: int = 10
    validation_policy = ValidationPolicy(
        ignore_warnings=True, 
        ignore_errors=False
    )
    
    def validate(self) -> List[ValidationResult]:
        results = super().validate()
        if self.threshold < 0 or self.threshold > 30:
            results.append(ValidationResult(
                field="threshold",
                message="Must be between 0 and 30",
                severity=ValidationSeverity.ERROR
            ))
        return results
```

**Validation:**
- [ ] Override `validate()` for custom rules
- [ ] Returns `List[ValidationResult]`
- [ ] Calls `super().validate()` first
- [ ] Uses appropriate `ValidationSeverity`

## Common Anti-Patterns to Avoid

### ❌ DON'T: Manual Plugin Registration
```python
# WRONG
agent.register_plugin("name", plugin_instance)
```

### ✅ DO: Inner Plugin Class
```python
# CORRECT
class MyAgent(BaseAgent):
    class Plugin(BaseAgent.Plugin):
        my_plugin = SomePlugin()
```

### ❌ DON'T: Super() Call After Other Code
```python
# WRONG
def setup(self):
    self.my_var = 10
    super().setup()  # Too late!
```

### ✅ DO: Super() Call First
```python
# CORRECT
def setup(self):
    super().setup()  # Always first!
    self.my_var = 10
```

### ❌ DON'T: Wrong Method Name
```python
# WRONG - PeriodicAgent using execute()
class MyAgent(PeriodicProcessAgent):
    def execute(self):  # Should be runner()!
        pass
```

### ✅ DO: Correct Method Name
```python
# CORRECT
class MyAgent(PeriodicProcessAgent):
    def runner(self):  # Correct for PeriodicAgent
        super().runner()
        # logic
```

### ❌ DON'T: Print Statements
```python
# WRONG
print("Agent started")
```

### ✅ DO: Use Logger
```python
# CORRECT
self.logger.info("Agent started")
```

## Testing Patterns

Use `MagicMock` for testing agents:
```python
from unittest.mock import MagicMock

state_events = BaseAgent.StateEvents(
    MagicMock(), MagicMock(), MagicMock()
)
control_events = BaseAgent.ControlEvents(
    MagicMock(), MagicMock(), MagicMock()
)
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

**Validation:**
- [ ] Tests use MagicMock for events and channels
- [ ] Tests cover lifecycle methods
- [ ] Tests verify super() call ordering
- [ ] Tests check configuration validation

## Reference Examples

Always consult these examples for patterns:
- `examples/example_periodic_agent.py` - PeriodicAgent pattern
- `examples/example_base_agent.py` - BaseAgent pattern
- `examples/example_pool_agent.py` - PoolAgent pattern
- `test/test_base_agent.py` - Testing patterns
