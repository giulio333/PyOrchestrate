---
title: Standalone Agent
---

# Standalone Agent

This example demonstrates how to use a PyOrchestrate agent in standalone mode, without the need for an orchestrator.

## Overview

PyOrchestrate allows you to use agents in two main modes:
1. Managed by an orchestrator (orchestrated mode)
2. Running autonomously (standalone mode)

The standalone mode is particularly useful when:
- You need a single agent for a specific operation
- You want to test an agent before integrating it into a more complex system
- You're creating a small application that doesn't require a full orchestrator

## Agent Implementation

Let's create a simple periodic agent called `SimpleCounterAgent` that counts up to a configured limit:

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

The `runner` method executes periodically based on the configured interval, incrementing and logging the counter value.

::: tip Configuration Tip
PyOrchestrate agents use a nested `Config` class pattern for configuration. When extending an agent, you can override built-in attributes like `execution_interval` and `limit` through your custom `Config` class. This maintains type safety and enables proper parameter validation.
:::

## Running in Standalone Mode

To run the agent in standalone mode, create a main file that starts and manages the agent:

```python
if __name__ == "__main__":
    # Create and start the agent
    agent = SimpleCounterAgent()
    agent.start()
    
    # The join() method waits for the agent to complete
    agent.join()
    
    print("Agent terminated.")
```

This code demonstrates how to:

1. Create an instance of the agent
2. Start the agent with the `start()` method
3. Wait for the agent to complete with the `join()` method

## Complete Example

Here's the complete example, including the agent and the main function:

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

if __name__ == "__main__":
    # Create and start the agent
    agent = SimpleCounterAgent()
    agent.start()
    
    # The join() method waits for the agent to complete
    agent.join()
    
    print("Agent terminated.")
```

This setup imports and registers the `WeatherCollector` agent with the orchestrator, which then manages its execution.