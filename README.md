# PyOrchestrate Framework

[![PyOrchestrate Test](https://github.com/giulio333/PyOrchestrate/actions/workflows/python-app.yml/badge.svg)](https://github.com/giulio333/PyOrchestrate/actions/workflows/python-app.yml)

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
here's a `FileWriter` agent that logs a message periodically:

``` python
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.base.periodic_agent import PeriodicProcessAgent


class FileWriterConfig(PeriodicProcessAgent.Config):
    """Process agent configuration class."""

    limit = 5
    execution_interval = 1
    directory = "/tmp"


class FileWriter(PeriodicProcessAgent[FileWriterConfig]):
    """Agent Class that logs a message periodically."""

    Config = FileWriterConfig

    def setup(self):
        """
        Setup method for the agent.
        """
        super().setup()
        self.logger.info(f"FileWriter {self.name} initialized. pid={self.pid}")
        self.logger.info(f"Working with directory: {self.config.directory}")

    def runner(self):
        """
        Runner method for the agent.
        """
        self.logger.info("Doing some work")

```

* * *

### Running with an Orchestrator

The **Orchestrator** coordinates agents and manages their lifecycle. Below is an example:

``` python
from PyOrchestrate.core.orchestrator import Orchestrator

if __name__ == "__main__":
    orchestrator = Orchestrator("CoolOrchestrator")

    # register agents
    orchestrator.register_agent(FileWriter, "FileWriter")

    # start agent
    orchestrator.start()

    # wait for agent to complete
    orchestrator.join()
```

* * *

## Configuration

Each agent has a `Config` class to customize behavior.

``` python
class CustomConfig(PeriodicProcessAgent.Config):
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
   Use `PeriodicProcessAgent` to collect sensor data every N seconds and save it to a database.

* * *

## Why Choose PyOrchestrate?

- Simplifies complex architectures with modular design.
- Reduces development time by providing reusable patterns.
- Scales from single tasks to intricate pipelines.

* * *

## Using the `start` Command

The PyOrchestrate framework includes a `start` command to create a new project structure. This command initializes a new project with the specified app name, creating the necessary directories and files.

### Command

``` bash
pyorchestrate start <app_name>
```

### Options

- `--help` or `-h`: Displays help information about the command.
- `--version` or `-v`: Displays the version of the PyOrchestrate framework.

### Project Structure

The `start` command creates the following project structure:

```
<app_name>/
    ├── models/
    ├── configurations/
    └── starter.py
```

- **App directory**: This is the main directory for the generated project, named after the specified app name.
  - `models`: A subdirectory where the user will insert the models of the specialized agents they want to create.
  - `configurations`: A subdirectory for storing the configurations of the agents.
  - `starter.py`: A file where the definition of how the orchestrator will manage the agents is provided.

### Example

To create a new project named `MyApp`, run the following command:

``` bash
pyorchestrate start MyApp
```

This will create a directory named `MyApp` with the necessary subdirectories and a `starter.py` file.

* * *

## Troubleshooting the `start` Command

If you encounter issues with the `start` command, here are some common problems and their solutions:

1. **Command not found**: Ensure that the `pyorchestrate` command is available in your PATH. You may need to install the package or adjust your environment variables.
2. **Permission denied**: Check your file system permissions. You may need to run the command with elevated privileges (e.g., using `sudo` on Unix-based systems).
3. **Invalid app name**: Ensure that the app name provided is a valid directory name and does not contain any restricted characters.
4. **Directory already exists**: If the specified app directory already exists, the command will not overwrite it. Choose a different app name or manually delete the existing directory.

For more details, refer to the documentation in the repository or the `usage.md` file.

