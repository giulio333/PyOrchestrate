# Quick Reference: BaseAgent vs Launcher System

> A concise visual summary of the comprehensive technical analysis

## 🎯 Core Concept

```
┌──────────────────────────────────────────────────────────────┐
│  PyOrchestrate = "Docker for Python Processes"               │
└──────────────────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
    BaseAgent              Launcher System
  (Execution Unit)      (Lifecycle Manager)
```

## 📊 Comparison Table

| Aspect | BaseAgent | Launcher System |
|--------|-----------|-----------------|
| **What** | Abstract class | Distributed component system |
| **Role** | Execution worker | Orchestration coordinator |
| **Focus** | Business logic | Lifecycle management |
| **Instances** | Many (1 per agent) | One (orchestrator + managers) |
| **Location** | Runs in child process/thread | Runs in main process |
| **Lifecycle** | Self-managed | Manages others |
| **Communication** | Unidirectional (→ Orchestrator) | Bidirectional (↔ Agents) |
| **Dependencies** | None | Manages dependency graph |
| **Timeout** | None | Built-in protection |
| **State** | Stateful (execution state) | Stateless (metadata only) |

## 🏗️ Architecture Overview

### BaseAgent Hierarchy

```
BaseClass
    │
    └── BaseAgent (ABC) ──┬─ abstract methods
            │             ├─ run() @final
            │             ├─ setup() template
            │             ├─ execute() @abstract
            │             └─ stop() @final
            │
            ├── BaseProcessAgent (multiprocessing.Process)
            │       ├── PeriodicProcessAgent
            │       ├── LoopingProcessAgent
            │       └── PoolProcessAgent
            │
            └── BaseThreadAgent (threading.Thread)
                    ├── PeriodicThreadAgent
                    └── LoopingThreadAgent
```

### Launcher System Architecture

```
Orchestrator
    ├── AgentLifecycleManager ──┬─ register_agent()
    │                           ├─ start_agent() [with timeout]
    │                           └─ stop_agent()
    │
    ├── OMemory ───────────────── AgentEntry ──┬─ Metadata storage
    │                                           ├─ initialize_agent() [factory]
    │                                           └─ Proxy methods (start, stop, join)
    │
    ├── DependencyGraph ────────┬─ add_dependency()
    │                           ├─ validate() [cycles, missing]
    │                           └─ topological_sort()
    │
    ├── WorkerPoolScheduler ────── max_workers enforcement
    │
    ├── MessageRouter ──────────── Agent messages → Events
    │
    └── EventBus ───────────────┬─ Event dispatch
                                ├─ Callback management
                                └─ EventStore (history)
```

## 🔄 Key Interaction Flow

```
USER CODE
    │
    ├─ orchestrator.register_agent(MyAgent, "name", config)
    │      │
    │      └─> AgentLifecycleManager.register_agent()
    │              │
    │              └─> OMemory.add_agent()
    │                      │
    │                      └─> Creates AgentEntry
    │                           (metadata only, NO instance yet)
    │
    ├─ orchestrator.start()
    │      │
    │      ├─> validate_dependencies()
    │      ├─> topological_sort() → ordered agents
    │      └─> WorkerPoolScheduler.schedule_agents()
    │              │
    │              └─> For each agent:
    │                      │
    │                      ├─ AgentEntry.initialize_agent()
    │                      │    (creates BaseAgent instance)
    │                      │
    │                      ├─ AgentEntry.start()
    │                      │    │
    │                      │    └─> multiprocessing.Process.start()
    │                      │         │
    │                      │         └─> In new process:
    │                      │                  BaseAgent.run()
    │                      │                      ├─ setup()
    │                      │                      ├─ execute()
    │                      │                      └─ cleanup
    │                      │
    │                      └─ Wait for start_event (with timeout)
    │
    └─ orchestrator.join()
           └─> Wait for all agents to complete
```

## 🎨 Design Patterns Used

### Common to Both

| Pattern | BaseAgent | Launcher System |
|---------|-----------|-----------------|
| **Template Method** | `run()` defines skeleton | `start_agent()` defines skeleton |
| **Factory** | Implicit (subclasses) | Explicit (`initialize_agent()`) |
| **Dependency Injection** | Config, Plugin, Events | Config, Plugin, Events |
| **Event-Driven** | state_events, control_events | OrchestratorEvent, callbacks |
| **Separation of Concerns** | lifecycle ≠ business logic | metadata ≠ instances |

### Unique Patterns

**BaseAgent:**
- **Strategy Pattern**: Different agent types (Periodic, Looping, Pool)
- **Observer Pattern**: Lifecycle events (start, ready, close)

**Launcher System:**
- **Facade Pattern**: Orchestrator hides complexity
- **Mediator Pattern**: MessageRouter coordinates communication
- **Registry Pattern**: OMemory stores agent metadata
- **Builder Pattern**: AgentEntry builds instances

## 📝 Common Similarities

### ✅ Both Use:

1. **Inner Class Pattern**
   ```python
   class Config(ParentClass.Config):
       field: type = default
   
   class Plugin(ParentClass.Plugin):
       plugin_name = PluginInstance()
   ```

2. **BaseClass Inheritance**
   - Provides logging, validation, config, plugin infrastructure

3. **Event Synchronization**
   - multiprocessing.Event or threading.Event based on type

4. **Loguru Logging**
   - Unified logging across all components

5. **Validation Framework**
   - Config validation with ValidationResult

6. **Plugin Manager**
   - Automatic plugin lifecycle (initialize → finalize)

## ⚡ Key Differences

### 1. Execution Context

```
BaseAgent:
┌─────────────────────────┐
│  Main Process           │
│                         │
│  Orchestrator creates   │
└─────────┬───────────────┘
          │ spawns
          ▼
┌─────────────────────────┐
│  Child Process/Thread   │
│                         │
│  BaseAgent.run()        │
│  - Business logic HERE  │
└─────────────────────────┘

Launcher System:
┌─────────────────────────┐
│  Main Process           │
│                         │
│  Orchestrator           │
│  - Coordination HERE    │
│  - No business logic    │
└─────────────────────────┘
```

### 2. Responsibility Split

```
┌────────────────────────────────────────────────────────┐
│                    WHAT vs HOW                         │
├────────────────────────────────────────────────────────┤
│  BaseAgent answers:      │  Launcher answers:          │
│  • WHAT to execute       │  • HOW to start/stop        │
│  • WHEN ready/done       │  • WHEN to start each       │
│  • HOW to do work        │  • WHO depends on WHO       │
│                          │  • WHERE to route events    │
└────────────────────────────────────────────────────────┘
```

### 3. Communication Direction

```
BaseAgent → MessageChannel → Orchestrator
   (sends events)           (receives & dispatches)

Orchestrator → control_events → BaseAgent
   (sends commands)           (receives & acts)
```

## 💡 Best Practices Summary

### For BaseAgent Developers

```python
✅ DO:
class MyAgent(PeriodicProcessAgent):
    class Config(PeriodicProcessAgent.Config):
        field: str = "value"  # Type hints!
    
    config: Config  # Type annotation!
    
    def setup(self):
        super().setup()  # ALWAYS FIRST!
        # your init
    
    def runner(self):
        super().runner()  # ALWAYS FIRST!
        # your logic
    
    def on_stop(self):
        # cleanup (no super needed)

❌ DON'T:
- Override run() (it's @final)
- Use print() (use self.logger)
- Manage other agents
- Block indefinitely
```

### For Orchestrator Users

```python
✅ DO:
orchestrator = Orchestrator(config=Orchestrator.Config(
    run_mode=RunMode.STOP_ON_EMPTY  # or DAEMON
))

# Register
orchestrator.register_agent(AgentClass, "name", custom_config)

# Dependencies
orchestrator.add_dependency("worker", ["db", "api"])

# Events
orchestrator.register_event(OrchestratorEvent.AGENT_READY, callback)

# Start
orchestrator.start()
orchestrator.join()

❌ DON'T:
- Skip validate_dependencies()
- Create circular dependencies
- Register after start()
- Manually create agent instances
```

## 🚀 Usage Pattern

### Minimal Example

```python
# Define agent
class Worker(PeriodicProcessAgent):
    class Config(PeriodicProcessAgent.Config):
        execution_interval: float = 5.0
    
    config: Config
    
    def runner(self):
        super().runner()
        self.logger.info("Working...")

# Use with orchestrator
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method("spawn")
    
    orchestrator = Orchestrator()
    orchestrator.register_agent(Worker, "worker")
    orchestrator.start()
    orchestrator.join()
```

### With Dependencies

```python
orchestrator = Orchestrator()

# Register in any order
orchestrator.register_agent(DatabaseAgent, "db")
orchestrator.register_agent(APIAgent, "api")
orchestrator.register_agent(WorkerAgent, "worker")

# Define dependencies (who needs who)
orchestrator.add_dependency("api", ["db"])      # api needs db
orchestrator.add_dependency("worker", ["api"])  # worker needs api

# Start in correct order automatically: db → api → worker
orchestrator.start()
```

## 📈 When to Use What

### Use BaseAgent When:
- ✅ Implementing business logic
- ✅ Creating reusable execution units
- ✅ Need isolation (process) or shared memory (thread)
- ✅ Want automatic lifecycle management
- ✅ Need plugin support

### Use Orchestrator When:
- ✅ Coordinating multiple agents
- ✅ Managing dependencies
- ✅ Need timeout protection
- ✅ Want centralized event tracking
- ✅ Need CLI control interface

## 🎓 Learning Path

1. **Start Here**: Read this summary
2. **Dive Deeper**: Full reports (Italian/English)
3. **See It Work**: Examples in `examples/`
4. **Understand Tests**: Tests in `test/`
5. **Build Something**: Create your own agent

## 📚 Related Documentation

- [Full Italian Report](./baseagent-vs-launcher-analisi-comparativa.md) (1761 lines)
- [Full English Report](./baseagent-vs-launcher-comparative-analysis.md) (1032 lines)
- [Technical Reports Index](./README.md)
- [Main Documentation](../../README.md)
- [Examples](../../examples/)

---

**Quick Tip**: BaseAgent = Worker, Launcher = Manager. Workers do the work, Manager coordinates them.

**Last Updated**: October 31, 2025
