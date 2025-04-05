---
title: Orchestrator
editLink: true
---

# Orchestrator

The **Orchestrator** is a central component responsible for coordinating multiple **Agents** and managing their lifecycle. It ensures seamless communication among **Agents** and serves as a single point for controlling the entire flow.

::: tip
For **more information**, see this [link](../core/orchestrator/index.md).
:::

## Usage

Here's an example of how to use the Orchestrator in your application.

```python
from PyOrchestrate.core.orchestrator import Orchestrator
from my_project.models import Publisher, Subscriber

if __name__ == "__main__":
    orchestrator = Orchestrator("Orchestrator")

    # register agents
    orchestrator.register_agent(Publisher, "Publisher")
    orchestrator.register_agent(Subscriber, "Subscriber")

    # start agent
    orchestrator.start()

    # wait for agent to complete
    orchestrator.join()
```

As shown in the example, the Orchestrator is initialized with a name and can register, start, and join multiple agents.

## Overview

### Orchestrator Behavior

The Orchestrator is designed to manage the lifecycle of agents, including:

- **Initialization**: Setting up all registered agents.
- **Starting**: Activating agents to begin their tasks.
- **Monitoring**: Keeping track of agent states and performance.
- **Joining**: Waiting for agents to complete their tasks before proceeding.
- **Stopping**: Gracefully shutting down agents when needed.

### Configuration

The `Config` class is used by the Orchestrator to **create a configuration object for itself**. 

Available attributes are

| Attribute       | Type         | Description                                                                 |
|-----------------|--------------|-----------------------------------------------------------------------------|
| `check_interval`| int          | The interval (in seconds) at which the Orchestrator checks the status of agents. |
| `max_workers`   | int          | The maximum number of worker threads to use for executing tasks.            |
| `logger`        | LoggerConfig | The logger configuration object.                                            |

::: info Example
For example to create an Orchestrator with a maximum of 2 workers, you can do the following:

```python
o_config = Orchestrator.Config(max_workers=2)
orchestrator = Orchestrator(config=o_config)
```

If you don't provide custom values, the Orchestrator will use the default values defined in the `Config` class.
:::

### Event Manager

The Event Manager facilitates a set of events (`OrchestratorEvent`) that notify when something happens during the orchestration process (e.g., an agent completes). These events can be used as **signals** to perform specific actions (e.g., sending a message on Telegram).

### Why Use Orchestrator?

Is not mandatory to use the Orchestrator, but it provides several advantages. Using the Orchestrator can help you automate the management of multiple agents (threads or processes), making it easier to coordinate their activities and ensuring that they work together effectively.

## Registering Agents

The Orchestrator allows you to **register agents** using the `register_agent` method. This method takes the `agent_class`, `name` and some optional parameters as arguments.

```python
orchestrator.register_agent(Publisher, "Publisher")
```

All available parameters are


| Parameter        | Type         | Description                                                                 |
|------------------|--------------|-----------------------------------------------------------------------------|
| `agent_class`    | Agent Class  | The agent class to be registered.                                           |
| `name`           | str          | The name of the agent. If not provided, the class name will be used.        |
| `custom_config`  | Config       | A custom configuration object for the agent. If not provided, the default config will be used. |
| `custom_plugin`  | Plugin       | A custom plugin object for the agent. If not provided, the default plugin will be used. |
| `control_events` | list         | A list of control events to be used by the agent. If not provided, the default events will be used. |
| `state_events`  | list         | A list of state events to be used by the agent. If not provided, the default events will be used. |
| `event_manager` | EventManager | The event manager to be used by the agent. If not provided, the default event manager will be used. |
| `kwargs`        | dict         | Additional keyword arguments to be passed to the agent constructor.         |