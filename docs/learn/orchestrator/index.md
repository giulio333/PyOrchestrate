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

Available events are stored in the `OrchestratorEvent` class:

| Event Name                     | Arguments                                        | Description                               |
|--------------------------------|--------------------------------------------------|-------------------------------------------|
| `AGENT_STARTED`                |  `event_date`, `event_time`, `agent_name`        | Emitted when an agent starts.             |
| `AGENT_TERMINATED`             |    `event_date`, `event_time`, `agent_name`      | Emitted when an agent terminates.         |
| `ALL_AGENTS_TERMINATED`        |    `event_date`, `event_time`                    | Emitted when all agents have terminated.  |

### Why Use Orchestrator?

Is not mandatory to use the Orchestrator, but it provides several advantages. Using the Orchestrator can help you automate the management of multiple agents (threads or processes), making it easier to coordinate their activities and ensuring that they work together effectively.

## Validation

The `Config` class provides a `validate` method that can be overridden to implement custom validation logic.

```python
class Config(BaseClassConfig):
    """Configuration with a single custom field and simple validation."""

    threshold: int = 10

    def validate(self):
        results = super().validate()

        # raise validation ERROR if threshold is not between 0 and 30
        if self.threshold < 0 or self.threshold > 30:
            results.append(
                ValidationResult(
                    field="threshold",
                    is_valid=False,
                    message="Threshold must be between 0 and 30.",
                    severity=ValidationSeverity.ERROR,
                )
            )
        return results
```

### Validation Policy

You can also override the `validation_policy` attribute to define a custom validation policy for your agent.

```python
from PyOrchestrate.core.utilities.validation import ValidationPolicy # [!code focus]

class Config(BaseClassConfig):
    """Configuration with a single custom field and simple validation."""

    threshold: int = 10
    validation_policy = ValidationPolicy(ignore_warnings=False, ignore_errors=False) # [!code focus]
```

### Validation Severity

The `ValidationResult` class provides a `severity` attribute that can be used to define the severity of the validation error.

The severity can be one of the following:

| Severity       | Description |
| ------------- |  :---- |
| `ValidationSeverity.WARNING` | The Agent will still start, but you’ll get a log message letting you know something might need attention. |
| `ValidationSeverity.ERROR` | The Agent won’t start, and an error will be logged.|
| `ValidationSeverity.CRITICAL` | Essential checks that must **never** be ignored. |

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
| `msg_channel`  | MessageChannel | The message channel to be used by the agent. If not provided, the Orchestrator's default message channel will be used. |
| `kwargs`        | dict         | Additional keyword arguments to be passed to the agent constructor.         |

If you don't provide optional parameters, the Orchestrator will use the default values defined in the `Agent` class.

### Example

You can create multiple Agents of the same Agent class, each with its own configuration:

```python
custom_config = Publisher.Config(output_file="custom_file.txt")

orchestrator.register_agent(Publisher, "Pub1")
orchestrator.register_agent(Publisher, "Pub2")
orchestrator.register_agent(Publisher, "Pub3", custom_config=custom_config)
```

In this example, we create three `Publisher` agents. The first two use default settings, while the third writes to a custom output file.

::: tip
For more details on Agent's **Configuration**, **StateEvents** etc. check out the [Agent Overview](../agents/index.md#overview).
:::