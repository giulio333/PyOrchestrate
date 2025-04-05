---
title: Orchestrator
editLink: true
---

# Orchestrator

The **Orchestrator** is the component in charge of supervising and coordinating your **Agents**. It takes care of starting them, managing their lifecycle, and making sure everything runs smoothly — whether you're using threads, processes, or a mix of both.

## 👥 Registering Agents

![alt text](./reg.png)

Before anything else, you need to **register** the Agents you want the Orchestrator to manage. This is done using the `register_agent()` method, which lets you provide the Agent class and an optional name. Once registered, the Orchestrator knows how to launch and manage each one.

::: tip Behind the scenes
When you register an Agent, the Orchestrator wraps it in an `AgentEntry` object that stores all the important details: class, config, plugins, events, and parameters. This makes it easy to start, stop, or even restart the Agent later.
:::

You can also restart a previously registered Agent using its `restart()` method, which stops, joins, and then relaunches the instance. This is useful for recovering Agents or re-executing isolated logic during runtime.

If you don’t provide control or state events, the Orchestrator will create them for you automatically and initialize them in a ready state.

::: tip
If you're looking for more details about Agent parameters, check out the [Agent documentation](../../agents/index.md).
:::

## ⚙️ How Agent Execution Works

After registering your Agents, the Orchestrator follows a series of steps to launch and manage them:

- **Step 1 – Check dependencies**: it ensures that all declared Agent dependencies exist and that there are no circular references. This produces an execution order where each Agent starts only after its prerequisites.

- **Step 2 – Start the Agents**: using the topological order, the Orchestrator initializes each Agent and starts it (as a process or thread). A `AGENT_STARTED` event is emitted when the Agent is running.

- **Step 3 – Monitor execution**: during runtime, the Orchestrator keeps an eye on all active Agents. When one finishes, it emits an `AGENT_TERMINATED` event and, if needed, starts another one from the queue.

- **Step 4 – Wrap things up**: once all Agents have completed and the queue is empty, a final `ALL_AGENTS_TERMINATED` event is emitted.

- **Step 5 – Wait for completion**: you can call `join()` to block the main thread until all Agents are done. Or use `simple_join()` if you just want to wait without managing events or dependencies.

## 🚦 Running Agents in Parallel with Limits

The Orchestrator supports **concurrency limits** to avoid overloading your system. You can define a `max_workers` value to cap how many Agents can run at the same time.

If the limit is reached, the extra Agents are placed in a queue. As soon as a slot frees up, the next waiting Agent is started automatically. This helps keep your system balanced and responsive.

## 🔔 Reacting to Events

As Agents run, the Orchestrator emits events at key moments — when they start, stop, or when everything is done. These events flow through an **Event Manager**, and you can hook into them to trigger alerts, logs, dashboards, or custom reactions.

This makes your system not only coordinated, but also observable and responsive to change.

## 🧱 Advanced Features and Observability

You can optionally organize your Agents into **Groups**, allowing you to logically separate them by function, priority, or execution phase. A Group is simply a named collection of Agent names. You can add or remove Agents from groups and later retrieve all instances in a group. This is useful for batch operations or context-based orchestration.

At any moment, you can ask the Orchestrator to report the status of all Agents: whether they’re running, what their process/thread ID is, and more.

The Orchestrator also maintains an internal history of all events for each Agent — including `start`, `stop`, and `join` — complete with timestamps. This history can be retrieved at any time using the `get_agent_stats(name)` method and is particularly useful for auditing, debugging, or tracking execution timelines.

You can even use one Orchestrator as an Agent inside another, allowing you to build **hierarchical orchestration layers**, where a top-level Orchestrator supervises others that manage their own subprocesses or threads.

If an Agent crashes or encounters an unhandled exception, the Orchestrator will still detect its termination. You can inspect its status or decide to manually restart it using the `restart()` method. This allows for basic fault tolerance and recovery strategies in more resilient systems.

## ⚙️ Customizing the Behavior

You can adjust how the Orchestrator behaves using its configuration `Orchestrator.Config`:

- `check_interval`: how often it checks the status of running Agents
- `max_workers`: how many Agents can run in parallel

## 💤 A Simpler Way to Wait

If you don’t need advanced lifecycle control or event tracking, the Orchestrator also offers a `simple_join()` method. It just waits for all Agents to finish — no queues, no events, just a clean wait until the job is done.

## 📊 Seeing What’s Happening

At any moment, you can ask the Orchestrator to report the status of all Agents: whether they’re running, what their process/thread ID is, and more.

It also logs each Agent’s lifecycle, including events like `start`, `stop`, and `join`, along with timestamps. This makes debugging and monitoring much easier, especially in long-running or production systems.