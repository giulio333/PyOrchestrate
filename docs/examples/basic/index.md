---
title: Weather Collector Agent
---

# Weather Collector Agent Example

This example demonstrates how to create an agent that periodically collects weather data from a weather API and logs the result.

## Overview

Imagine you require an agent that fetches weather information every 10 seconds. In this scenario, the built-in `PeriodicAgent` is ideal since it executes a function at regular intervals.

## Project Initialization

Start by creating a new PyOrchestrate project with the following command:

```bash
PyOrchestrate.cli start weather_collector
```

After execution, your project structure should look like this:

```plaintext
weather_collector/
├── models/
├── config/
├── starter.py
```

## Configuration Setup

In the `models` directory, create a configuration class named `WCConfig`:

```python
from PyOrchestrate.core.agent.periodic_agent import PeriodicProcessAgent

class WCConfig(PeriodicProcessAgent.Config):
    limit: int = 2
    execution_interval: float = 2
    url: str = "https://catfact.ninja/fact"
```

Here, `WCConfig` inherits from `PeriodicProcessAgent.Config`. The properties `limit` and `execution_interval` are provided by the base class, while `url` is a custom field. This configuration enables the agent to query the provided URL every `execution_interval` seconds for a maximum of `limit` iterations.

## Agent Implementation

Next, in the `models` directory, create an agent called `WeatherCollector`:

```python
import requests
from PyOrchestrate.core.agent.periodic_agent import PeriodicProcessAgent
from PyOrchestrate.core.base.exceptions import RecoverableException

from configurations.weather_config import WCConfig

class WeatherCollector(PeriodicProcessAgent[WCConfig]):

    config = WCConfig  # Associate the configuration class with the agent
    config: Config # Type hint for the config attribute

    def setup(self):
        super().setup()
        self.logger.info("Initializing WeatherCollector configuration...")

    def runner(self):
        self.logger.info(f"Requesting data from {self.config.url}...")

        try:
            response = requests.get(self.config.url)
            response.raise_for_status()
            data = response.json()
            self.logger.info(f"Received data: {data}")
        except requests.RequestException as e:
            raise RecoverableException(f"Request error: {e}")
```

The `runner` method executes periodically and logs the response. If any request fails, it raises a `RecoverableException` which prevents the agent from stopping.

::: tip Configuration Tip
When adding a new agent, you can override the `Config` attribute to use a custom configuration class, as shown with `WCConfig`.
:::

## Orchestrator Integration

Finally, update `starter.py` to register the new agent:

```python
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Imports
from PyOrchestrate.core.orchestrator import Orchestrator
from models.weathercollector import WeatherCollector

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.register_agent(WeatherCollector, "WeatherCollector")
    orchestrator.start()
    orchestrator.join()
```

This setup imports and registers the `WeatherCollector` agent with the orchestrator, which then manages its execution.