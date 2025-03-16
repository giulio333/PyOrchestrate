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

It serves three main purposes:

| Purpose       | Description |
| ------------- |  :---- |
| built-in attributes | can be customized by users to control the orchestrator's behavior. |
| user-defined attributes | provides a flexible space for users to add custom attributes. |
| attributes validation | provides a validate method that can be overridden to implement custom validation logic. |

::: info Example
For example `MyOrchestrator` class defines its own configuration class via parent's' `Config` class.

```python
class MyOrchestrator(Orchestrator):

    class Config(Orchestrator.Config): # [!code focus]
        retry = True # [!code focus]
        max_workers = 5 # [!code focus]

    config: Config
```
:::