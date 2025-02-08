---
title: BaseAgent
---

# BaseAgent

The **BaseAgent** is the foundation of all other agents in PyOrchestrate. It provides the basic structure for any custom agent.

## Why use BaseAgent?

Use it as a starting point to create your own agents with completely custom behavior.

## Usage

You can create a custom agent by inheriting from the `BaseProcessAgent` or `BaseThreadAgent` class.

| Method | Description | Override |
|--------|-------------| ---------|
| [execute](#execute) | Define the core logic of the agent. | Required :green_circle: |
| [setup](#setup) | Perform any setup operations required by the agent. | Optional :orange_circle: |
| [on_stop](#on-stop) | Implement custom logic during external shutdown request. | Optional :orange_circle: |
| [on_close](#on-close) | Implement custom logic during the agent’s shutdown. | Optional :orange_circle: |

::: tip Important
Make sure to call the parent method **for each overridden** method.

```python{3}
class CustomAgent(BaseProcessAgent):
    def setup(self):
        super().setup()
        # Custom setup logic
```
:::

## Inheritance

The `BaseProcessAgent` and `BaseThreadAgent` classes inherit from the `BaseAgent` class.

This is the shared structure of both classes.

```mermaid
classDiagram
    class BaseClass {
    }

    class BaseAgent {
        +run()
        +setup()
        +execute()
        +stop()
        +validate_config()
        +on_stop()
        +on_close()
    }

    class BaseProcessAgent {
    }
    class BaseThreadAgent {
    }

    BaseClass <|-- BaseAgent
    BaseAgent <|-- BaseProcessAgent
    BaseAgent <|-- BaseThreadAgent
```

To learn more about `BaseClass` click here.

## Sequence Diagram

The sequence diagram below illustrates the lifecycle of the `BaseAgent` after it is started.

```mermaid
sequenceDiagram
    participant Agent as BaseAgent
    participant Config as Config
    participant StateEvents as StateEvents
    participant ControlEvents as ControlEvents
    participant EventManager as EventManager

    Agent->>EventManager: emit(AGENT_START)
    Agent->>Config: validate_config()
    Agent->>ControlEvents: setup_event.wait()
    activate ControlEvents
    ControlEvents-->>Agent: control event triggered
    deactivate ControlEvents
    Agent->>Agent: setup()
    Agent->>EventManager: emit(AGENT_SETUP)
    Agent->>StateEvents: ready_event.set()
    Agent->>ControlEvents: execute_event.wait()
    activate ControlEvents
    ControlEvents-->>Agent: control event triggered
    deactivate ControlEvents
    Agent->>Agent: execute()
    Agent->>Agent: on_close()
    Agent->>EventManager: emit(AGENT_CLOSE)
    Agent->>StateEvents: close_event.set()
```

## Configuration

The `BaseAgent` class defines its own configuration object via the `Config` class.

| Attribute | Default | Description |
|-----------|---------|-------------|
| logger_config | `LoggerConfig` | Defines configuration for the logger. |

To learn more about the configuration object, click [here](../index.md#configuration).

## Control Events

The `BaseAgent` class defines its own control events object via the `ControlEvents` class.

| Attribute | Description |
|-----------|-------------|
| setup_event | Event to trigger the setup phase. |
| execute_event | Event to trigger the execution phase. |
| stop_event | Event to trigger the stop phase. |

To learn more about control events, click [here](../index.md#controlevents).

## State Events

The `BaseAgent` class defines its own state events object via the `StateEvents` class.

| Attribute | Description |
|-----------|-------------|
| ready_event | Event to signal that the agent is ready to start. |
| close_event | Event to signal that the agent is closing. |

To learn more about state events, click [here](../index.md#stateevents).

## Use Case

When no predefined agent meets your requirements, the `BaseAgent` is ideal for implementing custom logic.

## Methods

### run

```python
@final
```

This is the entry point for all agents, encapsulating their entire lifecycle and handling the low-level execution logic. In essence, the `run()` method in BaseAgent overrides the run method from `threading.Thread` or `multiprocessing.Process`.

It provides [execute](#execute) method to be overridden by the derived class to define the core logic of the agent.

::: warning Do not override
Marked as `@final` to prevent overriding in derived class ensuring that the core logic remains consistent across all agents.
:::

### setup
```python
@template
```

This method is called before the agent starts running. It can be overridden to perform any setup operations required by the agent.

::: tip Control Events
The setup method waits for the `control_events.setup_event` to be triggered, giving external systems the ability to manage when the setup phase starts.
:::

::: tip
Be sure to call the parent method if you override it.
:::

### execute

```python
@abstractmethod
```

This method is called by the `run()` method to execute the core logic of the agent. It must be overridden by the derived class to define the agent's behavior.

::: tip
Be sure to call the parent method.
:::

### stop

```python
@final
```

This method is called to stop the agent from external systems. 

Keep in mind that agents will not stop immediately. They will complete the current iteration of the `execute` method before stopping.

::: warning Do not override
Marked as `@final` to prevent overriding in derived class ensuring that the core logic remains consistent across all agents.
:::

::: tip
To implement custom logic during the agent’s shutdown, override the [on_stop](#on_stop) method in your derived class.
:::

### on_stop

```python
@optional
```

This method is called when the agent is stopped. It can be overridden to implement custom logic during the agent’s shutdown.

### on_close

```python
@optional
```

This method is called when the agent is closed. It can be overridden to implement custom logic during the agent’s shutdown.

## Attributes

### Logger

```python
logger: Logger
```

The logger object for the agent. Available levels are `DEBUG`, `INFO`, `SUCCESS`, `WARNING`, `ERROR`, and `CRITICAL`.

### State Events

```python
state_events: BaseAgent.StateEvents
```

The state events object for the agent.

### Control Events

```python
control_events: BaseAgent.ControlEvents
```

The control events object for the agent.

### Config

```python
config: BaseAgent.Config
```

The configuration object for the agent.

## Example

In this example, we create a custom agent that monitors a log file for a specific keyword.


```python
from PyOrchestrate.core.agent import BaseProcessAgent

class MyConfig(BaseProcessAgent.Config):
    log_file: str = "application.log"
    keyword: str = "ERROR"

class LogMonitorAgent(BaseProcessAgent["MyConfig"]):
    Config = MyConfig

    def setup(self):
        """
        Ensure the log file exists.
        """
        super().setup()

        self.logger.info(f"Initializing LogMonitorAgent for file: {self.config.log_file}")
        try:
            with open(self.config.log_file, "r") as f:
                self.logger.info("Log file found.")
        except FileNotFoundError:
            self.logger.error(f"Log file {self.config.log_file} does not exist.")
            raise

    def execute(self):
        """
        Monitor the log file for the specified keyword.
        """
        super().execute()

        self.logger.info(f"Monitoring for keyword: '{self.config.keyword}'")
        try:
            with open(self.config.log_file, "r") as f:
                for line in f:
                    if self.config.keyword in line:
                        self.logger.warning(f"Keyword found: {line.strip()}")
        except Exception as e:
            self.logger.error(f"Error reading the log file: {e}")

    def on_stop(self):
        """
        Log the agent's shutdown.
        """
        self.logger.info("LogMonitorAgent stopped.")
```

## Advanced Usage

For a deeper dive into how agents work and their advanced use cases, explore the **Advanced Insights section**.