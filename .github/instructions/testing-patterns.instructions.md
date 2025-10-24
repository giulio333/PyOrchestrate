---
applyTo: "test/**/*.py"
description: "Testing patterns and requirements for PyOrchestrate components"
---

# Testing Pattern Rules

## Core Testing Philosophy

PyOrchestrate tests use **unittest** framework with **MagicMock** for mocking lifecycle components. All tests should be deterministic, isolated, and comprehensive.

## Test File Structure

```
test/
├── __init__.py
├── test_base_agent.py           # BaseAgent testing
├── test_looping_agent.py        # LoopingAgent testing
├── test_orchestrator.py         # Orchestrator testing
├── test_memory.py               # OMemory testing
├── test_event_store.py          # EventStore testing
├── test_communication_plugin.py # Plugin testing
└── test_messaging_client.py     # MessageChannel testing
```

**Validation:**
- [ ] One test file per module
- [ ] `test_` prefix for all test files
- [ ] Clear, descriptive test names
- [ ] Organized by component type

## MagicMock Pattern for Agents

### Basic Agent Test Setup
```python
import unittest
from unittest.mock import MagicMock
from PyOrchestrate.core.agent import BaseAgent, PeriodicProcessAgent

class TestMyAgent(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Mock state events
        self.state_events = BaseAgent.StateEvents(
            start_event=MagicMock(),
            ready_event=MagicMock(),
            close_event=MagicMock()
        )
        
        # Mock control events
        self.control_events = BaseAgent.ControlEvents(
            stop_event=MagicMock(),
            pause_event=MagicMock(),
            resume_event=MagicMock()
        )
        
        # Mock message channel
        self.msg_channel = MagicMock()
        
        # Create config
        self.config = MyAgent.Config(
            execution_interval=1.0,
            custom_field="test_value"
        )
        
        # Create plugin (if needed)
        self.plugin = MyAgent.Plugin()
        
        # Create agent with mocks
        self.agent = MyAgent(
            name="test_agent",
            config=self.config,
            plugin=self.plugin,
            a_type="process",
            state_events=self.state_events,
            control_events=self.control_events,
            msg_channel=self.msg_channel
        )
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self.agent, 'on_stop'):
            self.agent.on_stop()
```

**Validation:**
- [ ] All events mocked with MagicMock
- [ ] Message channel mocked
- [ ] Config properly instantiated
- [ ] Plugin instantiated if used
- [ ] Proper cleanup in tearDown

## Testing Lifecycle Methods

### Test Setup Method
```python
def test_setup(self):
    """Test agent setup"""
    # Call setup
    self.agent.setup()
    
    # Verify initialization
    self.assertIsNotNone(self.agent.logger)
    self.assertEqual(self.agent.state, AgentState.READY)
    
    # Verify custom initialization
    self.assertTrue(hasattr(self.agent, 'custom_attribute'))
```

### Test Runner/Execute Method
```python
def test_runner(self):
    """Test periodic execution"""
    # Setup first
    self.agent.setup()
    
    # Call runner
    self.agent.runner()
    
    # Verify business logic executed
    self.assertEqual(self.agent.counter, 1)
    
    # Verify logging
    # Can check logger calls if needed

def test_execute(self):
    """Test continuous execution"""
    # For LoopingAgent
    self.agent.setup()
    
    # Execute once
    self.agent.execute()
    
    # Verify state changes
    self.assertTrue(self.agent.executed)
```

### Test on_stop Method
```python
def test_on_stop(self):
    """Test cleanup on stop"""
    # Setup first
    self.agent.setup()
    
    # Stop
    self.agent.on_stop()
    
    # Verify cleanup
    self.assertIsNone(self.agent.resource)
    self.assertEqual(
        self.agent.termination_status,
        AgentTerminationStatus.SUCCESS
    )
```

**Validation:**
- [ ] Tests call methods in correct order
- [ ] Tests verify state transitions
- [ ] Tests check business logic
- [ ] Tests verify cleanup

## Testing Super() Call Order

### Critical: Verify Super() Calls First
```python
def test_setup_super_call_order(self):
    """Verify super().setup() called first"""
    with patch.object(
        BaseAgent, 
        'setup', 
        wraps=self.agent.setup
    ) as mock_super:
        self.agent.setup()
        mock_super.assert_called_once()

def test_runner_super_call_order(self):
    """Verify super().runner() called first"""
    self.agent.setup()
    
    with patch.object(
        PeriodicProcessAgent,
        'runner',
        wraps=self.agent.runner
    ) as mock_super:
        self.agent.runner()
        mock_super.assert_called_once()
```

**Validation:**
- [ ] Tests verify super() is called
- [ ] Tests ensure correct call order
- [ ] Tests use patch.object with wraps

## Testing Configuration

### Test Config Validation
```python
def test_config_validation_success(self):
    """Test valid configuration"""
    config = MyAgent.Config(threshold=15)
    results = config.validate()
    
    # Should have no errors
    errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
    self.assertEqual(len(errors), 0)

def test_config_validation_error(self):
    """Test invalid configuration"""
    config = MyAgent.Config(threshold=100)  # Out of range
    results = config.validate()
    
    # Should have errors
    errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
    self.assertGreater(len(errors), 0)
    self.assertIn("threshold", errors[0].field)
```

### Test Config Inheritance
```python
def test_config_inheritance(self):
    """Test config inherits from parent"""
    self.assertIsInstance(
        self.config,
        PeriodicProcessAgent.Config
    )
    self.assertTrue(hasattr(self.config, 'execution_interval'))
```

**Validation:**
- [ ] Tests cover valid configurations
- [ ] Tests cover invalid configurations
- [ ] Tests verify validation rules
- [ ] Tests check inheritance chain

## Testing Plugins

### Test Plugin Lifecycle
```python
def test_plugin_setup(self):
    """Test plugin initialization"""
    # Plugin setup called automatically in agent.setup()
    self.agent.setup()
    
    # Verify plugin is ready
    self.assertTrue(self.agent.plugin.zmq_pub.is_ready())

def test_plugin_teardown(self):
    """Test plugin cleanup"""
    self.agent.setup()
    self.agent.on_stop()
    
    # Verify plugin cleaned up
    # Check resources released
```

### Test Plugin Access
```python
def test_plugin_access(self):
    """Test accessing plugins"""
    self.agent.setup()
    
    # Access via self.plugin
    self.assertIsNotNone(self.agent.plugin)
    self.assertTrue(hasattr(self.agent.plugin, 'zmq_pub'))
    
    # Use plugin
    self.agent.plugin.zmq_pub.send(b"test")
```

**Validation:**
- [ ] Tests verify plugin initialization
- [ ] Tests check plugin access pattern
- [ ] Tests verify plugin cleanup
- [ ] Tests mock external resources

## Testing Orchestrator

### Test Agent Registration
```python
def test_register_agent(self):
    """Test agent registration"""
    orchestrator = Orchestrator()
    
    orchestrator.register_agent(TestAgent, "test_agent")
    
    # Verify registration
    self.assertIn("test_agent", orchestrator.memory.agents)

def test_register_agent_with_config(self):
    """Test registration with custom config"""
    orchestrator = Orchestrator()
    custom_config = TestAgent.Config(execution_interval=2.0)
    
    orchestrator.register_agent(
        TestAgent,
        "test_agent",
        custom_config=custom_config
    )
    
    # Verify config applied
    agent_entry = orchestrator.memory.agents["test_agent"]
    self.assertEqual(
        agent_entry.config.execution_interval,
        2.0
    )
```

### Test Dependencies
```python
def test_add_dependency(self):
    """Test adding dependencies"""
    orchestrator = Orchestrator()
    orchestrator.register_agent(Agent1, "a1")
    orchestrator.register_agent(Agent2, "a2")
    
    orchestrator.add_dependency("a1", "a2")
    
    # Verify dependency
    self.assertIn("a2", orchestrator.memory.dependencies["a1"])

def test_circular_dependency_detection(self):
    """Test circular dependency rejection"""
    orchestrator = Orchestrator()
    orchestrator.register_agent(Agent1, "a1")
    orchestrator.register_agent(Agent2, "a2")
    orchestrator.register_agent(Agent3, "a3")
    
    orchestrator.add_dependency("a1", "a2")
    orchestrator.add_dependency("a2", "a3")
    
    # This should raise an error
    with self.assertRaises(ValueError):
        orchestrator.add_dependency("a3", "a1")
```

### Test Event System
```python
def test_event_registration(self):
    """Test event callback registration"""
    orchestrator = Orchestrator()
    callback = MagicMock()
    
    orchestrator.register_event(
        OrchestratorEvent.AGENT_READY,
        callback
    )
    
    # Trigger event (in actual implementation)
    # Verify callback called
    # callback.assert_called_once()
```

**Validation:**
- [ ] Tests cover registration scenarios
- [ ] Tests verify dependency logic
- [ ] Tests check event system
- [ ] Tests validate error conditions

## Testing Error Handling

### Test Recoverable Exceptions
```python
def test_recoverable_exception(self):
    """Test recoverable error handling"""
    from PyOrchestrate.core.base.exceptions import RecoverableException
    
    with self.assertRaises(RecoverableException):
        self.agent.setup()
        self.agent.runner()  # Raises recoverable error
```

### Test Termination Status
```python
def test_error_termination_status(self):
    """Test termination status on error"""
    self.agent.setup()
    
    # Simulate error
    self.agent._simulate_error()
    
    self.agent.on_stop()
    
    self.assertEqual(
        self.agent.termination_status,
        AgentTerminationStatus.ERROR
    )
```

**Validation:**
- [ ] Tests cover exception scenarios
- [ ] Tests verify error propagation
- [ ] Tests check termination status
- [ ] Tests validate error logging

## Test Coverage Requirements

### Minimum Coverage Targets
- **Core modules**: 90%+ coverage
- **Agent classes**: 85%+ coverage
- **Utility functions**: 80%+ coverage
- **Integration tests**: Critical paths covered

### Running Coverage
```bash
# Run tests with coverage
coverage run -m pytest test/

# Generate report
coverage report

# HTML report
coverage html
```

**Validation:**
- [ ] Coverage meets minimum targets
- [ ] Critical paths tested
- [ ] Edge cases covered
- [ ] Integration scenarios tested

## Common Testing Anti-Patterns to Avoid

### ❌ DON'T: Test Implementation Details
```python
# WRONG - testing internal variables
def test_internal_counter(self):
    self.assertEqual(self.agent._internal_counter, 0)
```

### ✅ DO: Test Behavior
```python
# CORRECT - testing observable behavior
def test_execution_count(self):
    self.agent.runner()
    self.agent.runner()
    self.assertEqual(self.agent.execution_count, 2)
```

### ❌ DON'T: Use Real Resources
```python
# WRONG - actual database connection
def test_database(self):
    self.agent.plugin.db.connect("real_database")
```

### ✅ DO: Mock External Resources
```python
# CORRECT - mocked database
@patch('psycopg2.connect')
def test_database(self, mock_connect):
    mock_connect.return_value = MagicMock()
    self.agent.plugin.db.connect("test_db")
```

### ❌ DON'T: Tests with Side Effects
```python
# WRONG - modifies global state
def test_config(self):
    global_config.update(test_values)
```

### ✅ DO: Isolated Tests
```python
# CORRECT - isolated test
def test_config(self):
    local_config = Config(test_values)
    # Test with local config
```

## Integration Testing

### Test Agent-Orchestrator Integration
```python
def test_agent_orchestrator_integration(self):
    """Test agent running in orchestrator"""
    orchestrator = Orchestrator()
    orchestrator.register_agent(TestAgent, "test")
    
    # Start in background thread for testing
    import threading
    thread = threading.Thread(target=orchestrator.start)
    thread.daemon = True
    thread.start()
    
    # Wait for agent ready
    time.sleep(2)
    
    # Verify agent is running
    self.assertIn("test", orchestrator.memory.agents)
    
    # Cleanup
    orchestrator.shutdown()
    thread.join(timeout=5)
```

**Validation:**
- [ ] Integration tests cover key flows
- [ ] Tests verify component interaction
- [ ] Tests handle timing appropriately
- [ ] Tests clean up resources

## Reference Test Examples

Always consult these examples:
- `test/test_base_agent.py` - Agent testing patterns
- `test/test_orchestrator.py` - Orchestrator testing
- `test/test_communication_plugin.py` - Plugin testing
- `test/test_memory.py` - Memory and state testing
