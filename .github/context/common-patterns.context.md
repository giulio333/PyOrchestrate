# Common PyOrchestrate Patterns Quick Reference

This document provides quick reference for frequently used patterns in PyOrchestrate.

## Agent Creation Patterns

### Periodic Process Agent
```python
from PyOrchestrate.core.agent import PeriodicProcessAgent

class MyAgent(PeriodicProcessAgent):
    class Config(PeriodicProcessAgent.Config):
        execution_interval: float = 5.0
        custom_field: str = "value"
    
    config: Config
    
    def setup(self):
        super().setup()
        self.logger.info("Agent initialized")
    
    def runner(self):
        super().runner()
        self.logger.info("Executing task")
```

### Looping Thread Agent
```python
from PyOrchestrate.core.agent import LoopingThreadAgent

class MyAgent(LoopingThreadAgent):
    class Config(LoopingThreadAgent.Config):
        custom_field: str = "value"
    
    config: Config
    
    def setup(self):
        super().setup()
        self.running = True
    
    def execute(self):
        super().execute()
        while self.running:
            # Continuous work
            time.sleep(0.1)
```

### Pool Process Agent
```python
from PyOrchestrate.core.agent import PoolProcessAgent

class WorkerAgent(PoolProcessAgent):
    class Config(PoolProcessAgent.Config):
        pool_size: int = 4
        execution_interval: float = 1.0
    
    config: Config
    
    def runner(self):
        super().runner()
        # Worker processes this
        self.process_work()
```

## Plugin Patterns

### ZeroMQ PubSub
```python
from PyOrchestrate.core.plugins.com import ZeroMQPubSub
import zmq

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
```

### ZeroMQ Push-Pull
```python
from PyOrchestrate.core.plugins.com import ZeroMQPushPull
import zmq

class Producer(PeriodicProcessAgent):
    class Plugin(PeriodicProcessAgent.Plugin):
        push = ZeroMQPushPull("tcp://*:5556", zmq.PUSH)
    
    plugin: Plugin

class Worker(LoopingProcessAgent):
    class Plugin(LoopingProcessAgent.Plugin):
        pull = ZeroMQPushPull("tcp://localhost:5556", zmq.PULL)
    
    plugin: Plugin
```

### Custom Plugin
```python
from PyOrchestrate.core.plugins.plugin_protocols import PluginProtocol

class DatabasePlugin(PluginProtocol):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
    
    def setup(self) -> None:
        import psycopg2
        self.connection = psycopg2.connect(self.connection_string)
    
    def teardown(self) -> None:
        if self.connection:
            self.connection.close()
    
    def is_ready(self) -> bool:
        return self.connection is not None

class MyAgent(PeriodicProcessAgent):
    class Plugin(PeriodicProcessAgent.Plugin):
        db = DatabasePlugin("postgresql://localhost/mydb")
    
    plugin: Plugin
```

## Orchestrator Patterns

### Basic Orchestrator Setup
```python
from PyOrchestrate.core.orchestrator import Orchestrator

orchestrator = Orchestrator()

# Register agents
orchestrator.register_agent(Agent1, "agent1")
orchestrator.register_agent(Agent2, "agent2")

# Add dependencies
orchestrator.add_dependency("agent1", "agent2")

# Start
orchestrator.start()
orchestrator.join()
```

### With Custom Configuration
```python
orchestrator = Orchestrator()

config = Agent1.Config(
    execution_interval=2.0,
    custom_field="value"
)

orchestrator.register_agent(
    Agent1,
    "agent1",
    custom_config=config
)
```

### With Event Callbacks
```python
from PyOrchestrate.core.utilities import OrchestratorEvent

def on_agent_ready(agent_name, event_date, event_time):
    print(f"{agent_name} is ready")

orchestrator.register_event(
    OrchestratorEvent.AGENT_READY,
    on_agent_ready
)
```

### Daemon Mode
```python
from PyOrchestrate.core.utilities import RunMode

config = Orchestrator.Config(run_mode=RunMode.DAEMON)
orchestrator = Orchestrator(config=config)
```

## Configuration Patterns

### Basic Config
```python
class Config(PeriodicProcessAgent.Config):
    api_url: str = "https://api.example.com"
    timeout: int = 30
    retry_count: int = 3
```

### With Validation
```python
from PyOrchestrate.core.utilities import (
    ValidationResult,
    ValidationSeverity,
    ValidationPolicy
)

class Config(PeriodicProcessAgent.Config):
    threshold: int = 10
    validation_policy = ValidationPolicy(
        ignore_warnings=True,
        ignore_errors=False
    )
    
    def validate(self) -> List[ValidationResult]:
        results = super().validate()
        if self.threshold < 0 or self.threshold > 100:
            results.append(ValidationResult(
                field="threshold",
                message="Must be between 0 and 100",
                severity=ValidationSeverity.ERROR
            ))
        return results
```

## Error Handling Patterns

### Recoverable Exceptions
```python
from PyOrchestrate.core.base.exceptions import RecoverableException

def runner(self):
    super().runner()
    try:
        result = self.api_call()
    except TemporaryError as e:
        raise RecoverableException(f"Temporary failure: {e}")
```

### Termination Status
```python
from PyOrchestrate.core.utilities import AgentTerminationStatus

def on_stop(self):
    if self.completed_successfully:
        self.termination_status = AgentTerminationStatus.SUCCESS
    elif self.has_warnings:
        self.termination_status = AgentTerminationStatus.WARNING
    elif self.has_errors:
        self.termination_status = AgentTerminationStatus.ERROR
    else:
        self.termination_status = AgentTerminationStatus.CRITICAL
```

## Logging Patterns

### Basic Logging
```python
def runner(self):
    super().runner()
    self.logger.info("Starting task")
    self.logger.debug("Debug details", extra_data="value")
    self.logger.warning("Warning message")
    self.logger.error("Error occurred", error=str(e))
```

### Structured Logging
```python
self.logger.info(
    "Processing item",
    item_id=item.id,
    status=item.status,
    duration=elapsed_time
)
```

## Testing Patterns

### Basic Agent Test
```python
import unittest
from unittest.mock import MagicMock

class TestMyAgent(unittest.TestCase):
    def setUp(self):
        self.state_events = BaseAgent.StateEvents(
            MagicMock(), MagicMock(), MagicMock()
        )
        self.control_events = BaseAgent.ControlEvents(
            MagicMock(), MagicMock(), MagicMock()
        )
        self.msg_channel = MagicMock()
        self.config = MyAgent.Config()
        self.plugin = MyAgent.Plugin()
        
        self.agent = MyAgent(
            name="test",
            config=self.config,
            plugin=self.plugin,
            a_type="process",
            state_events=self.state_events,
            control_events=self.control_events,
            msg_channel=self.msg_channel
        )
    
    def test_setup(self):
        self.agent.setup()
        self.assertIsNotNone(self.agent.logger)
```

## Decision Trees

### When to Use Process vs Thread?
- **Use Process** if:
  - CPU-intensive operations
  - Need memory isolation
  - Working with non-thread-safe libraries
  - Parallel computation

- **Use Thread** if:
  - I/O-bound operations
  - Need shared memory
  - Lightweight concurrency
  - Frequent inter-agent communication

### When to Use Periodic vs Looping?
- **Use PeriodicAgent** if:
  - Scheduled execution (every N seconds)
  - Fixed interval tasks
  - Rate-limited operations
  - Batch processing

- **Use LoopingAgent** if:
  - Continuous monitoring
  - Event-driven processing
  - Real-time responsiveness
  - Tight control loops

### When to Use PoolAgent?
- **Use PoolAgent** if:
  - Multiple independent workers needed
  - Work distribution required
  - Parallel task processing
  - Load balancing across processes

## Quick Checklist for New Agents

- [ ] Inner Config class with type hints
- [ ] `config: Config` type annotation
- [ ] Inner Plugin class (if using plugins)
- [ ] `plugin: Plugin` type annotation
- [ ] `super()` called FIRST in all lifecycle methods
- [ ] Correct method name (runner vs execute)
- [ ] Use `self.logger`, not `print()`
- [ ] Proper error handling with RecoverableException
- [ ] Configuration validation if needed
- [ ] Tests with MagicMock pattern

## Import Reference

```python
# Agents
from PyOrchestrate.core.agent import (
    BaseAgent,
    PeriodicProcessAgent,
    PeriodicThreadAgent,
    LoopingProcessAgent,
    LoopingThreadAgent,
    PoolProcessAgent
)

# Orchestrator
from PyOrchestrate.core.orchestrator import Orchestrator

# Plugins
from PyOrchestrate.core.plugins.com import (
    ZeroMQPubSub,
    ZeroMQPushPull,
    ZeroMQReqRep,
    ZeroMQPair,
    ZeroMQRouterDealer
)
from PyOrchestrate.core.plugins.heartbeat import HeartbeatPlugin
from PyOrchestrate.core.plugins.plugin_protocols import PluginProtocol

# Utilities
from PyOrchestrate.core.utilities import (
    OrchestratorEvent,
    AgentTerminationStatus,
    RunMode,
    ValidationResult,
    ValidationSeverity,
    ValidationPolicy
)

# Exceptions
from PyOrchestrate.core.base.exceptions import RecoverableException

# ZeroMQ
import zmq
```

## File Locations

- **Core Agents**: `PyOrchestrate/core/agent/`
- **Orchestrator**: `PyOrchestrate/core/orchestrator/`
- **Plugins**: `PyOrchestrate/core/plugins/`
- **Utilities**: `PyOrchestrate/core/utilities/`
- **Examples**: `examples/`
- **Tests**: `test/`
