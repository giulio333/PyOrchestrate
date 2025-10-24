# PyOrchestrate Anti-Patterns

This document lists common mistakes and anti-patterns to avoid when developing with PyOrchestrate.

## Agent Development Anti-Patterns

### ❌ Missing Config Inner Class
```python
# WRONG - No Config inner class
class MyAgent(PeriodicProcessAgent):
    def __init__(self, interval):
        self.interval = interval
```

**Why it's wrong**: Violates framework pattern, breaks configuration management

**✅ Correct approach**:
```python
class MyAgent(PeriodicProcessAgent):
    class Config(PeriodicProcessAgent.Config):
        execution_interval: float = 5.0
    
    config: Config
```

### ❌ Super() Called After Other Code
```python
# WRONG - super() not first
def setup(self):
    self.my_var = 10
    super().setup()  # Too late!
```

**Why it's wrong**: Parent initialization must happen first

**✅ Correct approach**:
```python
def setup(self):
    super().setup()  # Always first!
    self.my_var = 10
```

### ❌ Wrong Method Name for Agent Type
```python
# WRONG - PeriodicAgent using execute()
class MyAgent(PeriodicProcessAgent):
    def execute(self):  # Should be runner()!
        pass
```

**Why it's wrong**: PeriodicAgent calls `runner()`, not `execute()`

**✅ Correct approach**:
```python
class MyAgent(PeriodicProcessAgent):
    def runner(self):
        super().runner()
        # logic
```

### ❌ Missing Type Annotations
```python
# WRONG - No type annotations
class MyAgent(PeriodicProcessAgent):
    class Config(PeriodicProcessAgent.Config):
        field = "value"  # No type hint
    
    # Missing: config: Config
```

**Why it's wrong**: Breaks type checking and IDE support

**✅ Correct approach**:
```python
class MyAgent(PeriodicProcessAgent):
    class Config(PeriodicProcessAgent.Config):
        field: str = "value"
    
    config: Config
```

### ❌ Using print() Instead of Logger
```python
# WRONG - Using print
def runner(self):
    super().runner()
    print("Task completed")
```

**Why it's wrong**: Bypasses logging system, loses context

**✅ Correct approach**:
```python
def runner(self):
    super().runner()
    self.logger.info("Task completed")
```

### ❌ Direct Agent-to-Agent Communication
```python
# WRONG - Direct communication
class Agent1(BaseAgent):
    def runner(self):
        super().runner()
        agent2.process(self.data)  # Direct call!
```

**Why it's wrong**: Violates orchestration pattern, creates coupling

**✅ Correct approach**:
```python
class Agent1(BaseAgent):
    def runner(self):
        super().runner()
        # Use message channel
        self.msg_channel.send("data_ready", self.data)
```

## Plugin Anti-Patterns

### ❌ Manual Plugin Registration
```python
# WRONG - Manual registration
class MyAgent(BaseAgent):
    def setup(self):
        super().setup()
        self.register_plugin("zmq", ZeroMQPubSub(...))
```

**Why it's wrong**: Bypasses framework plugin management

**✅ Correct approach**:
```python
class MyAgent(BaseAgent):
    class Plugin(BaseAgent.Plugin):
        zmq = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
    
    plugin: Plugin
```

### ❌ Manual Plugin Lifecycle Management
```python
# WRONG - Manual setup
def setup(self):
    super().setup()
    self.plugin.zmq.setup()  # Framework does this!
```

**Why it's wrong**: Framework handles plugin lifecycle automatically

**✅ Correct approach**:
```python
def setup(self):
    super().setup()
    # Plugins already set up, just use them
    self.plugin.zmq.send(b"ready")
```

### ❌ Using Plugin Before Setup
```python
# WRONG - Too early
class MyAgent(BaseAgent):
    class Plugin(BaseAgent.Plugin):
        zmq = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plugin.zmq.send(b"hello")  # Not ready yet!
```

**Why it's wrong**: Plugins not initialized until setup()

**✅ Correct approach**:
```python
def setup(self):
    super().setup()
    # Now plugins are ready
    self.plugin.zmq.send(b"hello")
```

## Orchestrator Anti-Patterns

### ❌ Registering Events on Agents
```python
# WRONG - Event on agent
agent.register_event(OrchestratorEvent.AGENT_READY, callback)
```

**Why it's wrong**: Events should be orchestrator-level

**✅ Correct approach**:
```python
orchestrator.register_event(
    OrchestratorEvent.AGENT_READY,
    callback
)
```

### ❌ Circular Dependencies
```python
# WRONG - Creates cycle
orchestrator.add_dependency("a", "b")
orchestrator.add_dependency("b", "c")
orchestrator.add_dependency("c", "a")  # Circular!
```

**Why it's wrong**: Creates deadlock in startup sequence

**✅ Correct approach**:
```python
# Linear or tree structure
orchestrator.add_dependency("a", "b")
orchestrator.add_dependency("a", "c")
orchestrator.add_dependency("b", "d")
```

### ❌ Registering After Start
```python
# WRONG - Registration after start
orchestrator.start()
orchestrator.register_agent(LateAgent, "late")
```

**Why it's wrong**: Registration must happen before start

**✅ Correct approach**:
```python
orchestrator.register_agent(Agent1, "a1")
orchestrator.register_agent(Agent2, "a2")
orchestrator.start()
```

### ❌ Missing RunMode for Long-Running Services
```python
# WRONG - Default mode for service
orchestrator = Orchestrator()
# Will stop when agents finish!
```

**Why it's wrong**: STOP_ON_EMPTY inappropriate for services

**✅ Correct approach**:
```python
config = Orchestrator.Config(run_mode=RunMode.DAEMON)
orchestrator = Orchestrator(config=config)
```

## Configuration Anti-Patterns

### ❌ Missing Required Fields
```python
# WRONG - No execution_interval
class Config(PeriodicProcessAgent.Config):
    custom_field: str = "value"
    # Missing: execution_interval!
```

**Why it's wrong**: PeriodicAgent requires execution_interval

**✅ Correct approach**:
```python
class Config(PeriodicProcessAgent.Config):
    execution_interval: float = 5.0
    custom_field: str = "value"
```

### ❌ Not Calling super().validate()
```python
# WRONG - Skips parent validation
def validate(self) -> List[ValidationResult]:
    results = []  # Should call super()!
    # custom validation
    return results
```

**Why it's wrong**: Misses parent class validation rules

**✅ Correct approach**:
```python
def validate(self) -> List[ValidationResult]:
    results = super().validate()  # Get parent results
    # Add custom validation
    return results
```

### ❌ Validation Without Return
```python
# WRONG - No return
def validate(self) -> List[ValidationResult]:
    results = super().validate()
    if self.field < 0:
        print("Error!")  # Wrong!
```

**Why it's wrong**: Must return ValidationResult objects

**✅ Correct approach**:
```python
def validate(self) -> List[ValidationResult]:
    results = super().validate()
    if self.field < 0:
        results.append(ValidationResult(
            field="field",
            message="Must be positive",
            severity=ValidationSeverity.ERROR
        ))
    return results
```

## Error Handling Anti-Patterns

### ❌ Swallowing Exceptions
```python
# WRONG - Silent failure
def runner(self):
    super().runner()
    try:
        self.risky_operation()
    except Exception:
        pass  # Silently fails!
```

**Why it's wrong**: Hides failures, makes debugging impossible

**✅ Correct approach**:
```python
def runner(self):
    super().runner()
    try:
        self.risky_operation()
    except TemporaryError as e:
        raise RecoverableException(f"Failed: {e}")
    except Exception as e:
        self.logger.error("Critical error", error=str(e))
        raise
```

### ❌ Not Setting Termination Status
```python
# WRONG - No status set
def on_stop(self):
    self.cleanup()
    # Missing: termination status!
```

**Why it's wrong**: Orchestrator can't track agent outcomes

**✅ Correct approach**:
```python
def on_stop(self):
    self.cleanup()
    if self.error_occurred:
        self.termination_status = AgentTerminationStatus.ERROR
    else:
        self.termination_status = AgentTerminationStatus.SUCCESS
```

### ❌ Using Generic Exceptions
```python
# WRONG - Generic exception
def runner(self):
    super().runner()
    if self.should_retry:
        raise Exception("Try again")  # Too generic
```

**Why it's wrong**: Framework can't distinguish recoverable errors

**✅ Correct approach**:
```python
def runner(self):
    super().runner()
    if self.should_retry:
        raise RecoverableException("Temporary failure, retry")
```

## Testing Anti-Patterns

### ❌ Not Using MagicMock for Events
```python
# WRONG - Real events
class TestAgent(unittest.TestCase):
    def setUp(self):
        self.agent = MyAgent(
            name="test",
            state_events=BaseAgent.StateEvents(...),  # Real events!
        )
```

**Why it's wrong**: Creates actual threading objects, makes tests flaky

**✅ Correct approach**:
```python
def setUp(self):
    self.state_events = BaseAgent.StateEvents(
        MagicMock(), MagicMock(), MagicMock()
    )
    self.agent = MyAgent(
        name="test",
        state_events=self.state_events,
        # ...
    )
```

### ❌ Testing Implementation Details
```python
# WRONG - Testing private variables
def test_internal_state(self):
    self.agent.runner()
    self.assertEqual(self.agent._counter, 1)
```

**Why it's wrong**: Tests become brittle, tied to implementation

**✅ Correct approach**:
```python
def test_execution_behavior(self):
    self.agent.runner()
    # Test observable behavior
    self.assertTrue(self.agent.task_completed)
```

### ❌ Not Testing Super() Calls
```python
# WRONG - Doesn't verify super()
def test_setup(self):
    self.agent.setup()
    # Only tests custom logic
```

**Why it's wrong**: Critical framework pattern not validated

**✅ Correct approach**:
```python
def test_setup_super_call(self):
    with patch.object(
        BaseAgent,
        'setup',
        wraps=self.agent.setup
    ) as mock_super:
        self.agent.setup()
        mock_super.assert_called_once()
```

## Process vs Thread Choice Anti-Patterns

### ❌ Using Thread for CPU-Intensive Work
```python
# WRONG - CPU work in thread
class DataCruncher(PeriodicThreadAgent):
    def runner(self):
        super().runner()
        # Heavy CPU computation - GIL bound!
        self.crunch_numbers()
```

**Why it's wrong**: Python GIL limits CPU parallelism in threads

**✅ Correct approach**:
```python
class DataCruncher(PeriodicProcessAgent):
    def runner(self):
        super().runner()
        # CPU work in isolated process
        self.crunch_numbers()
```

### ❌ Using Process for Simple I/O
```python
# WRONG - Overkill for I/O
class LogReader(PeriodicProcessAgent):
    def runner(self):
        super().runner()
        # Just reading files
        self.read_logs()
```

**Why it's wrong**: Process overhead unnecessary for I/O

**✅ Correct approach**:
```python
class LogReader(PeriodicThreadAgent):
    def runner(self):
        super().runner()
        # I/O work fits thread model
        self.read_logs()
```

## ZeroMQ Anti-Patterns

### ❌ Wrong Socket Type Pairing
```python
# WRONG - PUB trying to receive
class BadPublisher(PeriodicProcessAgent):
    class Plugin(PeriodicProcessAgent.Plugin):
        pub = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
    
    def runner(self):
        super().runner()
        msg = self.plugin.pub.receive()  # PUB can't receive!
```

**Why it's wrong**: Socket types have specific roles

**✅ Correct approach**:
```python
# Use correct socket type
class Publisher(PeriodicProcessAgent):
    class Plugin(PeriodicProcessAgent.Plugin):
        pub = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
    
    def runner(self):
        super().runner()
        self.plugin.pub.send(b"message")  # Correct
```

### ❌ Blocking Receive in Periodic Agent
```python
# WRONG - Blocking receive
def runner(self):
    super().runner()
    msg = self.plugin.sub.receive()  # Blocks!
    # Won't return for next interval
```

**Why it's wrong**: Blocks periodic execution

**✅ Correct approach**:
```python
# Use LoopingAgent for continuous receive
class Subscriber(LoopingProcessAgent):
    def execute(self):
        super().execute()
        msg = self.plugin.sub.receive()  # OK in loop
```

## Memory Management Anti-Patterns

### ❌ Accumulating Unbounded State
```python
# WRONG - Grows forever
class MyAgent(PeriodicProcessAgent):
    def setup(self):
        super().setup()
        self.all_results = []
    
    def runner(self):
        super().runner()
        self.all_results.append(self.get_result())  # Memory leak!
```

**Why it's wrong**: Memory grows indefinitely

**✅ Correct approach**:
```python
def setup(self):
    super().setup()
    self.recent_results = deque(maxlen=1000)  # Bounded
```

### ❌ Not Cleaning Up Resources
```python
# WRONG - No cleanup
class MyAgent(BaseAgent):
    def setup(self):
        super().setup()
        self.file = open("data.txt", "w")
    
    # Missing on_stop()!
```

**Why it's wrong**: Resources leak on termination

**✅ Correct approach**:
```python
def setup(self):
    super().setup()
    self.file = open("data.txt", "w")

def on_stop(self):
    if self.file:
        self.file.close()
```

## Summary of Critical Rules

1. ✅ **ALWAYS** call `super()` first in lifecycle methods
2. ✅ **ALWAYS** use inner Config class with type hints
3. ✅ **ALWAYS** use inner Plugin class (not manual registration)
4. ✅ **ALWAYS** use `self.logger`, never `print()`
5. ✅ **ALWAYS** use correct method name (runner vs execute)
6. ✅ **ALWAYS** register events on Orchestrator, not agents
7. ✅ **ALWAYS** communicate via Orchestrator, not direct
8. ✅ **ALWAYS** validate configuration properly
9. ✅ **ALWAYS** handle errors with appropriate exceptions
10. ✅ **ALWAYS** clean up resources in on_stop()

## When in Doubt

1. Check `examples/` directory for reference implementations
2. Look at `test/` directory for testing patterns
3. Review `.github/instructions/` for detailed patterns
4. Consult `.github/copilot-instructions.md` for architecture
