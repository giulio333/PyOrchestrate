---
title: Agents
editLink: true
---

# Agents

**Agents** are the core execution units managed by the Orchestrator. 

Each Agent encapsulates a specific task and can run either in a separate **thread** or **process**. The Agent class provides a standardized lifecycle and configuration system, allowing you to focus solely on your business logic.

## 🟢 Getting Started

### Agent Types

![alt text](./types_l.svg){.light-only}
![alt text](./types_d.svg){.dark-only}

Agents can be implemented in different styles, depending on their intended behavior:

- **OneShotAgent**: performs a single task and then exits.
- **LoopingAgent**: continuously performs a task until externally stopped.
- **PeriodicAgent**: executes at regular time intervals.
- **EventAgent**: responds to external events or signals.
- **ScheduledAgent**: runs based on a predefined schedule.

Each one builds on top of the core logic provided by `BaseAgent`, inheriting its lifecycle and configuration support.

::: tip
To learn more about the different Agent types, check out the [Hierarchical Structure](../../agents/index.md#hierarchical-structure) section.
:::

### Configuration

Each Agent has a `Config` class that defines its settings, like how often it runs or where it saves output. You can override these defaults or extend the class for custom options, making Agents flexible and safe to use.

Built-in Agents use their configuration class to manage essential parameters. For example, the `LoopingAgent` defines options like loop interval and stop conditions in its config. 

::: tip Example
See the [LoopingAgent configuration object](../../learn/agents/built-in-agents/loopingagent.md#configuration) for details.
:::

### Plugin System

Agents support plugins to extend their capabilities. Plugins are automatically initialized and finalized with the Agent, and can be used to modularize logic or add monitoring, transformation, or communication features.

### Thread vs Process

Agents can run as:

- **Thread-based**: share memory, lightweight, best for I/O-bound tasks.
- **Process-based**: isolated, resilient, ideal for CPU-intensive or crash-prone tasks.

This is defined at the time of Agent creation and is managed internally by the Orchestrator.

## 🔁 Lifecycle

![alt text](./lifecycle_l.svg){.light-only}
![alt text](./lifecycle_d.svg){.dark-only}

All Agents follow a standardized lifecycle:

1. **Config Validation**  
   The Agent checks its configuration for correctness. If any issues are found, the Agent will not start.

2. **Setup**  
   Executed before the task starts. Use this step for initialization and preparation.

3. **Execution**  
   The core of the Agent. This is where the main task is performed — once, repeatedly, or on trigger.

4. **Stop**  
   When the Orchestrator requests a stop or the Agent finishes its tasks.

Throughout this lifecycle, internal and external events are used to synchronize actions and manage state transitions.

## 🧠 Observability and Events

Each Agent manages two kinds of event systems.

### State Events 

These represent the internal status of the Agent. They indicate key lifecycle transitions such as:

- when the Agent is starting
- when it's ready to execute
- when it has completed its task

These events are useful for **observing** the current state of each Agent and synchronizing other components in the system.

::: tip
To learn more about the different events, check out the [Agent State Events](../../agents/index.md#stateevents) section.
:::

### Control Events  

These allow the Orchestrator (or other Agents) to **drive** the Agent's lifecycle. They are used to signal when the Agent is allowed to:

- start the setup phase
- begin execution
- stop gracefully

Control events give you fine-grained control over each phase of execution, allowing custom orchestration strategies.

::: tip
To learn more about the different events, check out the [Agent Control Events](../../agents/index.md#controlevents) section.
:::

## 🧪 Validation and Safety

The configuration class of each Agent supports built-in validation. This ensures that incorrect parameters are caught before the Agent starts.

If validation fails, the Agent does not start, and the error is logged.

## 🔄 Grouping and Control

Agents can be grouped into **logical collections**, allowing the Orchestrator to manage them together. Groups can be used to filter Agents by function, priority, or lifecycle stage.

This enables bulk operations like restarting, stopping, or monitoring only a subset of Agents.