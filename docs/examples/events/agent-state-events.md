---
title: State Events Usage
---

# State Events Usage

This example demonstrates how to use agent state events to synchronize operations when running an agent in standalone mode (without an orchestrator).

## Overview

PyOrchestrate agents provide state events that can be used to wait for specific phases in the agent lifecycle. These events are particularly useful when running agents in standalone mode, allowing you to coordinate tasks based on the agent's current state.

In this example, we'll create a simple counter agent that counts up to a configured limit and show how to use its state events.

## Agent Implementation

Let's create a simple periodic agent called `SimpleCounterAgent`:

```python
from PyOrchestrate.core.agent import PeriodicProcessAgent


class SimpleCounterAgent(PeriodicProcessAgent):

    class Config(PeriodicProcessAgent.Config):
        # Maximum number to count to
        limit: int = 10
        # Interval between numbers in seconds
        execution_interval: float = 0.5

    config: Config

    def setup(self) -> None:
        """
        Agent initialization: logs the setup information.
        """
        super().setup()

        self.count = 0

    def runner(self) -> None:
        """
        Counts up to the configured maximum number with regular intervals.
        """
        super().runner()

        self.count += 1
        self.logger.info(f"Count: {self.count} of {self.config.limit}")
```

The `runner` method executes periodically based on the configured interval, incrementing and logging the counter value. This simple example lets us focus on the state events functionality.

::: tip Configuration Tip
When extending an agent, you can override the `Config` attribute to use a custom configuration class with your specific parameters, as shown in the example.
:::

## Using State Events

State events allow you to coordinate with an agent's lifecycle. When running an agent in standalone mode (not managed by an orchestrator), you can use these events to synchronize operations:

```python
if __name__ == "__main__":

    agent = SimpleCounterAgent()
    agent.start()

    agent.state_events.start_event.wait()
    print("Agent started.")

    agent.state_events.ready_event.wait()
    print("Agent ready.")

    agent.state_events.close_event.wait()
    print("Agent closed.")
```

This code demonstrates how to:

1. Wait for the agent to start (`start_event`) - the agent has begun initialization
2. Wait for the agent to be ready (`ready_event`) - the agent has completed setup and is executing its main function
3. Wait for the agent to close (`close_event`) - the agent has terminated its execution

These state events work for both process-based and thread-based agents, making them a powerful tool for coordinating operations in complex applications.