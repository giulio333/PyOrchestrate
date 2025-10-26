---
title: WorkerPoolScheduler
editLink: true
---

# WorkerPoolScheduler

The **WorkerPoolScheduler** enforces concurrency limits and manages the agent startup queue. It ensures that the system doesn't exceed the configured maximum number of concurrent running agents, automatically queuing and starting agents as resources become available.

## Purpose and Design

Without concurrency control, an orchestrator could attempt to start hundreds of agents simultaneously, overwhelming system resources (CPU, memory, network connections). The WorkerPoolScheduler prevents this by:

- Limiting how many agents run concurrently
- Queuing agents when the limit is reached
- Automatically starting queued agents when slots open up
- Tracking agent states throughout their lifecycle

## Core Responsibilities

| Responsibility | Description |
|---------------|-------------|
| **Concurrency Control** | Enforce `max_workers` limit on running agents |
| **Queue Management** | Queue agents waiting for available slots |
| **Automatic Scheduling** | Start queued agents when capacity available |
| **State Tracking** | Monitor pending, running, and completed agents |
| **Timeout Enforcement** | Apply `agent_start_timeout` configuration |

## Agent States

The WorkerPoolScheduler manages agents through three states:

```
PENDING → RUNNING → COMPLETED
   ↓         ↓          ↓
(queued) (executing) (terminated)
```

| State | Description | Counted Against max_workers |
|-------|-------------|---------------------------|
| **PENDING** | Agent waiting in queue for slot | No |
| **RUNNING** | Agent currently executing | Yes |
| **COMPLETED** | Agent has terminated | No |

## How It Works

### Starting Agents

When you start an agent:

1. **Check available slots**: Is current running count < `max_workers`?
2. **If YES**: Start agent immediately, increment running count
3. **If NO**: Add agent to pending queue

```python
# Start agent (may queue if pool full)
worker_pool.start_agent("agent_name")
```

### Agent Termination

When an agent terminates:

1. **Remove from running set**: Decrement running count
2. **Add to completed set**: Mark as done
3. **Check pending queue**: Are there agents waiting?
4. **If YES**: Start next queued agent (goto step 1 of Starting Agents)

```python
# Notify scheduler that agent terminated
worker_pool.on_agent_terminated("agent_name")
# Automatically starts next queued agent if any
```

### Completion Detection

Check if all agents have finished:

```python
if worker_pool.all_finished:
    print("All agents completed")
    # running_agents: 0
    # pending_queue: 0
```

```python
if worker_pool.all_finished:
    print("All agents completed")
    # running_agents: 0
    # pending_queue: 0
```

## Integration with Orchestrator

### During Orchestrator Start

The WorkerPoolScheduler works with the DependencyGraph to start agents:

```python
# Orchestrator.start() internally does:
# 1. Get dependency-ordered agent list from DependencyGraph
ordered_agents = dependency_graph.topological_sort(all_agent_names)
# Result: ["database", "cache", "api"] (dependency order)

# 2. Start agents via WorkerPoolScheduler
for agent_name in ordered_agents:
    worker_pool.start_agent(agent_name)
    # May start immediately or queue based on max_workers
```

**Result**: Agents respect both dependency order AND concurrency limits.

### During Orchestrator Join

The orchestrator monitors agent completion and notifies the scheduler:

```python
# Orchestrator.join() internally monitors agents
for agent_name in running_agents:
    if agent_terminated(agent_name):
        worker_pool.on_agent_terminated(agent_name)
        # Scheduler automatically starts next queued agent

# Check termination condition
if config.run_mode == RunMode.STOP_ON_EMPTY:
    if worker_pool.all_finished:
        break  # All done!
```

## Configuration

### max_workers Setting

Control how many agents run concurrently:

| Value | Use Case | Example |
|-------|----------|---------|
| **Low (2-5)** | Limited resources, sequential processing | Raspberry Pi, small VPS |
| **Moderate (10-20)** | Balanced workload, typical server | Default configuration |
| **High (50-100)** | High-throughput, powerful server | Data centers, cloud instances |
| **Unlimited** | No restrictions (use with caution) | Testing, development |

```python
# Conservative: Only 3 agents at once
config = OrchestratorConfig(max_workers=3)

# Default: 10 concurrent agents
config = OrchestratorConfig(max_workers=10)

# Aggressive: 50 concurrent agents
config = OrchestratorConfig(max_workers=50)
```

### Choosing the Right max_workers

**For CPU-Bound Agents**:
```python
import multiprocessing
config = OrchestratorConfig(
    max_workers=multiprocessing.cpu_count()
)
```

**For I/O-Bound Agents**:
```python
config = OrchestratorConfig(
    max_workers=multiprocessing.cpu_count() * 4
)
```

**For Memory-Constrained Systems**:
```python
import psutil

available_ram_gb = psutil.virtual_memory().available / (1024**3)
agent_memory_gb = 0.5  # Estimated per agent
max_workers = int(available_ram_gb / agent_memory_gb)

config = OrchestratorConfig(max_workers=max_workers)
```

## Common Use Cases

### Batch Processing with Limited Resources

Process many tasks with limited concurrency:

```python
config = OrchestratorConfig(max_workers=10)
orchestrator = Orchestrator(config=config)

# Register 1000 tasks
for i in range(1000):
    orchestrator.register_agent(TaskAgent, f"task_{i}")

orchestrator.start()
# Only 10 run at a time
# Remaining 990 are queued
# As each completes, next one starts

orchestrator.join()  # Waits for all 1000 to complete
```

### Priority Execution

Start high-priority agents first by registering them first:

```python
config = OrchestratorConfig(max_workers=5)
orchestrator = Orchestrator(config=config)

# High-priority agents (registered first, won't queue)
orchestrator.register_agent(CriticalAgent, "critical_1")
orchestrator.register_agent(CriticalAgent, "critical_2")

# Normal-priority agents (will queue if pool fills)
for i in range(20):
    orchestrator.register_agent(WorkerAgent, f"worker_{i}")

orchestrator.start()
# critical_1, critical_2 start immediately
# worker_0, worker_1, worker_2 start immediately (fills to max_workers=5)
# worker_3 through worker_19 are queued
```

### Wave-Based Processing

Process agents in waves:

```python
# Wave 1: Data collection (max 5 concurrent)
for i in range(10):
    orchestrator.register_agent(DataCollector, f"collector_{i}")

orchestrator.start()
orchestrator.join()  # Wait for wave 1

# Wave 2: Data processing (max 10 concurrent)
orchestrator.worker_pool.max_workers = 10
for i in range(20):
    orchestrator.register_agent(DataProcessor, f"processor_{i}")
# Continue orchestrator...
```

## Monitoring

### Pool Statistics

Monitor the scheduler's state:

```python
def get_pool_stats(orchestrator):
    pool = orchestrator.worker_pool
    
    return {
        "max_workers": pool.max_workers,
        "running": len(pool._running_agents),
        "queued": len(pool._pending_queue),
        "completed": len(pool._completed_agents),
        "utilization": len(pool._running_agents) / pool.max_workers * 100
    }

# Example output:
# {
#     "max_workers": 10,
#     "running": 8,
#     "queued": 15,
#     "completed": 27,
#     "utilization": 80.0%
# }
```

### Real-Time Monitoring

```python
import time

def monitor_pool(orchestrator, interval=5.0):
    while not orchestrator.worker_pool.all_finished:
        stats = get_pool_stats(orchestrator)
        print(f"Running: {stats['running']}/{stats['max_workers']} | "
              f"Queued: {stats['queued']} | "
              f"Completed: {stats['completed']}")
        time.sleep(interval)
```

## Error Handling

### Agent Start Failures

If an agent fails to start, the scheduler:
- Removes it from the running set
- Frees the slot for the next agent
- Logs the error
- Continues processing the queue

```python
# Agent fails to start
try:
    worker_pool.start_agent("problematic_agent")
except Exception as e:
    logger.error(f"Failed to start: {e}")
    # Slot is automatically freed
    # Next queued agent will start
```

### Queue Overflow Management

Monitor and handle large queues:

```python
if len(worker_pool._pending_queue) > 1000:
    logger.warning("Queue very large, consider increasing max_workers")
    
    # Option 1: Increase concurrency
    orchestrator.worker_pool.max_workers = 20
    
    # Option 2: Throttle agent registration
    # (pause adding more agents until queue shrinks)
```

## Performance Considerations

### Memory Usage

```
Low max_workers (e.g., 5)
    ↓
Fewer agents in memory
    ↓
Lower memory footprint, slower completion

High max_workers (e.g., 100)
    ↓
Many agents in memory
    ↓
Higher memory usage, faster completion
```

### CPU Utilization

For CPU-bound agents:
- `max_workers = CPU count` → 100% CPU utilization
- `max_workers > CPU count` → Context switching overhead
- `max_workers < CPU count` → Underutilized CPU

For I/O-bound agents:
- `max_workers` can exceed CPU count significantly
- Agents spend time waiting for I/O, not using CPU

### Queue Management Overhead

- Queue operations: **O(1)** (append/pop from deque)
- State tracking: **O(1)** (set operations)
- Thread-safe locking: Minimal overhead

The scheduler is highly efficient even with thousands of agents.

## Best Practices

### 1. Set Appropriate max_workers

```python
# ✅ Good: Based on system resources
max_workers = calculate_based_on_resources()

# ❌ Bad: Arbitrary number
max_workers = 999  # May overwhelm system
```

### 2. Monitor Queue Growth

```python
# Alert on unbounded queue growth
if len(orchestrator.worker_pool._pending_queue) > threshold:
    alert("Queue too large, investigate!")
```

### 3. Adjust max_workers Dynamically (Carefully)

```python
# Can adjust at runtime, but be careful
if system_load_low():
    orchestrator.worker_pool.max_workers = 20
else:
    orchestrator.worker_pool.max_workers = 5
```

### 4. Handle Startup Timeouts

```python
config = OrchestratorConfig(
    max_workers=10,
    agent_start_timeout=60.0  # Give agents time to start
)
```

## Integration with Other Managers

| Manager | Interaction |
|---------|-------------|
| **DependencyGraph** | Provides startup order → WorkerPoolScheduler enforces concurrency |
| **AgentLifecycleManager** | WorkerPoolScheduler calls lifecycle_manager.start_agent() |
| **OrchestratorEventBus** | Not directly related, but both receive termination notifications |

## See Also

- [AgentLifecycleManager](./lifecycle-manager.md) - Creates and starts agent instances
- [DependencyGraph](./dependency-graph.md) - Determines agent startup order
- [Orchestrator Internals](./index.md) - Architecture overview
