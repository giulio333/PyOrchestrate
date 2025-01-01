# PyOrchestrate Framework

**PyOrchestrate** is a Python framework designed to simplify the creation and management of multi-process and
multi-thread architectures. It provides a structured approach to orchestrating tasks, allowing developers to focus on
logic while the framework handles complexities like process and thread management.

## Features

- Centralized management via the **Orchestrator**.
- Flexible execution units: **Agents** (processes or threads).
- Hierarchical orchestration for complex systems.
- Predefined agent types like **PeriodicAgent**, **EventAgent**, and **ScheduledAgent**.
- Extensibility to customize behavior for specific needs.

* * *

## Quick Start

### Installation

Ensure Python 3.12+ is installed, then clone the repository and install the required dependencies:

``` bash
git clone https://github.com/yourusername/pyorchestrate.git cd pyorchestrate pip install -r requirements.txt
```

* * *

## Basic Usage

### Defining an Agent

Define a custom agent by inheriting from predefined agent classes like `PeriodicAgent` or `LoopingAgent`. For example,
here's a `WeatherCollector` agent that fetches data periodically:

``` python
from PyOrchestrate.core.base.periodic_agent import PeriodicAgent
from PyOrchestrate.core.base.base_agent import ProcessAgent

class WeatherCollector(PeriodicAgent["WeatherCollector.Config"], ProcessAgent["WeatherCollector.Config"]):
    """Agent to collect weather data periodically."""

    class Config(PeriodicAgent.Config):
        """Agent configuration."""
        
        output_file = output_file
        url = url
        execution_interval = 10  # seconds

    def setup(self):
        if not os.path.exists(self.config.output_file):
            with open(self.config.output_file, "w") as f:
                json.dump([], f)

    def runner(self):
        response = requests.get(self.config.url)
        data = response.json()
        with open(self.config.output_file, "r+") as f:
            records = json.load(f)
            records.append(data)
            f.seek(0)
            json.dump(records, f, indent=4)

```

* * *

### Running with an Orchestrator

The **Orchestrator** coordinates agents and manages their lifecycle. Below is an example:

``` python
from PyOrchestrate.core.orchestrator import Orchestrator
from models import WeatherCollector

if __name__ == "__main__":
    orchestrator = Orchestrator("Orchestrator")

    orchestrator.register_agent(WeatherCollector, "WeatherCollector")

    orchestrator.start()
    orchestrator.join()
```

* * *

## Configuration

Each agent has a `Config` class to customize behavior.

``` python
class CustomConfig(PeriodicAgent.Config):
    def __init__(self):
        super().__init__()
        self.execution_interval = 5  # every 5 seconds
```

* * *

## Example Use Cases

1. **Standalone Agent**  
   A standalone `OneShotAgent` processes a single task without orchestration.

2. **Hierarchical Orchestration**  
   The main orchestrator manages agents that themselves spawn threads for subtasks.

3. **Periodic Data Collection**  
   Use `PeriodicAgent` to collect sensor data every N seconds and save it to a database.

* * *

## Why Choose PyOrchestrate?

- Simplifies complex architectures with modular design.
- Reduces development time by providing reusable patterns.
- Scales from single tasks to intricate pipelines.

* * *

For more details, refer to the documentation in the repository or the `usage.md` file.

