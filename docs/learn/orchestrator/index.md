---
title: Orchestrator
editLink: true
---

# Orchestrator

The Orchestrator is a central component responsible for coordinating multiple agents and managing their lifecycle. 
It ensures seamless communication among agents and serves as a single point for controlling the entire flow.

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

The Orchestrator comes with a dedicated Configuration object, enabling you to define both required and custom attributes.

### Event Manager

The Event Manager facilitates a set of events (`OrchestratorEvent`) that notify when something happens during the orchestration process (e.g., an agent completes). These events can be used as **signals** to perform specific actions (e.g., sending a message on Telegram).

### Why Use Orchestrator?

Is not mandatory to use the Orchestrator, but it provides several advantages. Using the Orchestrator can help you automate the management of multiple agents (threads or processes), making it easier to coordinate their activities and ensuring that they work together effectively.

## Configuration

The `Config` class is used by the Orchestrator to **create a configuration object for itself**. 

Available attributes are:
- `check_interval`: (int) The interval (in seconds) at which the Orchestrator checks the status of agents.
- `max_workers`: (int) The maximum number of worker threads to use for executing tasks.
- `logger`: (LoggerConfig) The logger configuration object.

::: info Example
For example `MyOrchestrator` class defines its own configuration class via parent's' `Config` class.

```python
class MyOrchestrator(Orchestrator):

    class Config(Orchestrator.Config): # [!code focus]
        check_interval = 5 # [!code focus]
        max_workers = 2 # [!code focus]
        logger = LoggerConfig() # [!code focus]

    config: Config
```
:::

## Registering Agents

The Orchestrator allows you to register agents using the `register_agent` method. This method takes the agent class and some optional parameters as arguments.

```python
orchestrator.register_agent(Publisher, "Publisher")
```