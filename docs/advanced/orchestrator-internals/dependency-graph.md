---
title: DependencyGraph
editLink: true
---

# DependencyGraph

The **DependencyGraph** manages agent dependencies and determines the correct startup order. It ensures that agents are started in the right sequence, preventing issues where an agent tries to communicate with another agent that hasn't started yet.

## Purpose and Design

In multi-agent systems, agents often depend on other agents being ready before they can function properly. For example:
- A **DataProcessor** agent depends on a **DatabaseConnector** agent
- An **APIServer** agent depends on both **Database** and **Cache** agents
- Multiple **Worker** agents depend on a **Coordinator** agent

The DependencyGraph solves this by:
- Tracking dependencies between agents
- Validating that all dependencies can be satisfied
- Computing the correct startup order using topological sorting
- Detecting circular dependencies that would cause deadlocks

## Core Responsibilities

| Responsibility | Description |
|---------------|-------------|
| **Dependency Tracking** | Maintains relationships between agents |
| **Validation** | Checks for circular dependencies and missing agents |
| **Startup Ordering** | Computes topological sort for correct startup sequence |
| **Error Detection** | Identifies impossible dependency configurations |

## How It Works

### Dependency Declaration

Declare dependencies using the orchestrator's API:

```python
# AgentB depends on AgentA
orchestrator.add_dependency("AgentB", ["AgentA"])

# AgentC depends on both AgentA and AgentB
orchestrator.add_dependency("AgentC", ["AgentA", "AgentB"])
```

### Automatic Validation

Before starting agents, the orchestrator validates the dependency graph:

```python
orchestrator.validate_dependencies()
# Checks for:
# 1. Circular dependencies (A → B → A)
# 2. Missing dependencies (references to unregistered agents)
# 3. Invalid configurations
```

### Topological Sorting

The DependencyGraph computes the startup order:

```python
# Registered agents: ["AgentA", "AgentB", "AgentC"]
# Dependencies: B→A, C→[A,B]

ordered_agents = dependency_graph.topological_sort(agent_names)
# Result: ["AgentA", "AgentB", "AgentC"]
```

**Result**: Agents start in dependency order, ensuring dependencies are always ready.

## Validation and Error Detection

### Circular Dependencies

The DependencyGraph detects **circular dependencies** that would cause deadlocks:

```python
# Invalid configuration
orchestrator.add_dependency("AgentA", ["AgentB"])
orchestrator.add_dependency("AgentB", ["AgentA"])  # ❌ Circular!

try:
    orchestrator.validate_dependencies()
except ValueError as e:
    print(f"Error: {e}")
    # Output: "Circular dependency detected"
```

**Why this matters**: If AgentA waits for AgentB, and AgentB waits for AgentA, neither can start—resulting in a deadlock.

### Missing Dependencies

The graph also detects references to **unregistered agents**:

```python
orchestrator.register_agent(WorkerAgent, "worker")
orchestrator.add_dependency("worker", ["database"])  # ❌ database not registered

try:
    orchestrator.validate_dependencies()
except ValueError as e:
    print(f"Error: {e}")
    # Output: "Agent 'worker' depends on unregistered agent 'database'"
```

### Validation Timing

Validation occurs automatically during `orchestrator.start()`:

```python
orchestrator.start()
# Internally calls:
# 1. validate_dependencies()
# 2. topological_sort() to get order
# 3. Start agents in order
```

## Common Use Cases

### Linear Dependency Chain

Create a **pipeline** where each agent depends on the previous one:

```python
# Pipeline: DataCollector → DataProcessor → DataWriter
orchestrator.register_agent(DataCollector, "collector")
orchestrator.register_agent(DataProcessor, "processor")
orchestrator.register_agent(DataWriter, "writer")

orchestrator.add_dependency("processor", ["collector"])
orchestrator.add_dependency("writer", ["processor"])

orchestrator.start()
# Startup order: collector → processor → writer
```

**Use case**: Data processing pipelines, ETL workflows

### Diamond Dependency

Multiple agents depend on the same base agent:

```python
orchestrator.register_agent(DatabaseAgent, "database")
orchestrator.register_agent(CacheAgent, "cache")
orchestrator.register_agent(APIAgent, "api")
orchestrator.register_agent(MonitorAgent, "monitor")

# Both cache and monitor depend on database
orchestrator.add_dependency("cache", ["database"])
orchestrator.add_dependency("monitor", ["database"])

# API depends on both database and cache
orchestrator.add_dependency("api", ["database", "cache"])

orchestrator.start()
# Startup order: database → cache, monitor (parallel) → api
```

**Use case**: Microservices architecture, shared infrastructure

### Parallel Independent Agents

Agents with **no dependencies** start in parallel (limited by `max_workers`):

```python
# No dependencies = parallel startup
orchestrator.register_agent(WorkerAgent, "worker1")
orchestrator.register_agent(WorkerAgent, "worker2")
orchestrator.register_agent(WorkerAgent, "worker3")

orchestrator.start()
# All agents start simultaneously (respecting max_workers limit)
```

**Use case**: Worker pools, parallel task execution

## Integration with WorkerPoolScheduler

The DependencyGraph works in conjunction with the WorkerPoolScheduler to ensure both **correct ordering** and **controlled concurrency**:

| Component | Responsibility |
|-----------|---------------|
| **DependencyGraph** | Determines **startup order** (which agent starts first) |
| **WorkerPoolScheduler** | Enforces **concurrency limits** (how many agents run at once) |

**Example**:
- DependencyGraph says: "Start database, then cache, then api"
- WorkerPoolScheduler says: "But only start 2 at a time (max_workers=2)"
- Result: database and cache start first, api waits in queue

## Algorithms

The DependencyGraph uses two well-known graph algorithms:

### Cycle Detection

Uses **Depth-First Search (DFS)** to detect circular dependencies:
- Traverses the dependency graph
- Tracks visited nodes and recursion stack
- Detects back edges that indicate cycles
- **Time Complexity**: O(V + E)

### Topological Sorting

Uses **Kahn's Algorithm** to compute startup order:
- Builds in-degree map (how many dependencies each agent has)
- Starts with agents having zero dependencies
- Processes agents in order, reducing in-degrees
- **Time Complexity**: O(V + E)

Both algorithms run only once during orchestrator startup, so performance impact is minimal even with hundreds of agents.

## Best Practices

### 1. Declare Dependencies Explicitly

```python
# ✅ Good: Clear dependency declaration
orchestrator.add_dependency("processor", ["collector"])

# ❌ Bad: Implicit assumption without declaration
# (Processor assumes collector is ready but doesn't declare it)
```

### 2. Avoid Circular Dependencies

```python
# ❌ Bad: Creates deadlock
orchestrator.add_dependency("A", ["B"])
orchestrator.add_dependency("B", ["A"])

# ✅ Good: Use coordinator pattern
orchestrator.add_dependency("A", ["coordinator"])
orchestrator.add_dependency("B", ["coordinator"])
```

### 3. Validate Before Starting

```python
try:
    orchestrator.validate_dependencies()
except ValueError as e:
    logger.error(f"Invalid configuration: {e}")
    sys.exit(1)

orchestrator.start()
```

### 4. Document Complex Dependencies

```python
# Document the reason for dependencies
orchestrator.add_dependency(
    "api_server",
    ["database", "cache"]  # API needs both services ready
)
```

## See Also

- [AgentLifecycleManager](./lifecycle-manager.md) - Creates agents in dependency order
- [WorkerPoolScheduler](./worker-pool.md) - Manages concurrent execution
- [Orchestrator Internals](./index.md) - Architecture overview
