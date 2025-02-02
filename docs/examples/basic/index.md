---
title: Weather Collector Agent
---

Let's start with some basic examples to get you started with PyOrchestrate. These examples are simple and easy to understand, and they cover the basic concepts of PyOrchestrate.

# Simple Weather Collector Agent

Imagine you want to create an agent that collects weather data from a weather API every 10 seconds. This agent should print the weather data to log.

In this case, the built-in `PeriodicAgent` is a good choice. It is a simple agent that runs a function periodically.

### Initialize Project

First, create a PyOrchestrate project using the following command:

```bash
PyOrchestrate.cli start weather_collector
```

You should see the following project structure:

```plaintext
weather_collector/
├── models/
├── config/
├── starter.py
```

### Create Config

Create a new configuration class called `WCConfig` in the `models` directory:

```python
from PyOrchestrate.core.agent.periodic_agent import PeriodicProcessAgent


class WCConfig(PeriodicProcessAgent.Config):
    limit: int = 2
    execution_interval: float = 2
    url: str = "https://catfact.ninja/fact"
```

As you can see, the `WCConfig` class inherits from `PeriodicProcessAgent.Config` since we are creating a periodic agent. 

The `limit` and `execution_interval` are built-in attributes of the `PeriodicProcessAgent.Config` class. The `url` and `print_result` attributes are custom attributes that we added to the configuration.

So the agent will make a request to the `url` every `execution_interval` seconds for `limit=2` times.

### Create Agent

Now, create a new agent called `WeatherCollector` in the `models` directory:

```python
import requests
from PyOrchestrate.core.agent.periodic_agent import PeriodicProcessAgent
from PyOrchestrate.core.base.exceptions import RecoverableException

from configurations.weather_config import WCConfig


class WeatherCollector(PeriodicProcessAgent[WCConfig]):

    Config = WCConfig # Assign the configuration class to the agent

    def setup(self):
        super().setup()
        self.logger.info("Initial configuration of the WeatherCollector...")

    def runner(self):
        self.logger.info(f"Making request to {self.config.url}...")

        try:
            response = requests.get(self.config.url)
            response.raise_for_status()
            data = response.json()

            self.logger.info(f"Response: {data}")

        except requests.RequestException as e:
            raise RecoverableException(f"Error while requesting: {e}")
```

Our new agent inherits from `PeriodicProcessAgent`. The `runner` method is the method that will be executed periodically. 

If an exception is raised, the agent will raise a `RecoverableException`, which will not stop the agent (for demonstration purposes).

::: tip Config
When defining a new agent, you can override the `Config` class to use a custom configuration class. Just keep in mind that configuration 
classes must inherit from the base agent configuration class. In this case, from `PeriodicProcessAgent.Config` class.
:::

## Orchestrator

Now wen can import our new agent in the `starter.py` file:

```python
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Imports
from PyOrchestrate.core.orchestrator import Orchestrator
from models.weathercollector import WeatherCollector

if __name__ == "__main__":

    # Initialize Orchestrator
    orchestrator = Orchestrator()

    # Register Agents
    orchestrator.register_agent(WeatherCollector, "WeatherCollector")

    # Start Orchestrator
    orchestrator.start()

    # Join Agents
    orchestrator.join()
```

All you need to do is to import the new agent and register it in the orchestrator. The orchestrator will take care of the rest.