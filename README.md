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
- Plugin system for dynamic extension of agent functionalities, including communication plugins.

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

* * *

## Plugin System

The PyOrchestrate framework includes a plugin system that allows for dynamic extension of agent functionalities. This system supports various types of plugins, including communication plugins.

### Communication Plugins

Communication plugins enable agents to send and receive messages using different communication mechanisms. The following communication plugins are available:

- **ZeroMQPlugin**: Provides communication using ZeroMQ sockets.
- **HTTPPlugin**: Provides communication using HTTP requests.
- **RedisPubSubPlugin**: Provides communication using Redis Pub/Sub.
- **FileBasedPlugin**: Provides communication using file-based message passing.

### Example Usage

Here's an example of how to use the communication plugins with an agent:

``` python
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import BaseProcessAgent
from PyOrchestrate.core.agent.communication_plugins import ZeroMQPlugin, HTTPPlugin, RedisPubSubPlugin, FileBasedPlugin


class MyConfig(BaseProcessAgent.Config):
    log_file: str = "application.log"
    keyword: str = "ERROR"


class LogMonitorAgent(BaseProcessAgent[MyConfig]):

    Config = MyConfig

    def setup(self) -> None:
        """
        Ensure the log file exists.
        """
        super().setup()

        self.config.logger_config.level = "INFO"

        self.logger.info(
            f"Initializing LogMonitorAgent for file: {self.config.log_file}"
        )
        try:
            with open(self.config.log_file, "r") as f:
                self.logger.info("Log file found.")
        except FileNotFoundError:
            self.logger.error(f"Log file {self.config.log_file} does not exist.")
            raise

        # Register communication plugins
        self.register_plugin(ZeroMQPlugin("tcp://localhost:5555", zmq.REQ))
        self.register_plugin(HTTPPlugin("http://localhost:8000"))
        self.register_plugin(RedisPubSubPlugin("localhost", 6379, "log_channel"))
        self.register_plugin(FileBasedPlugin("/tmp/log_messages.txt"))

    def execute(self) -> None:
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
                        # Send message using communication plugins
                        self.get_plugin("ZeroMQPlugin").send(line.strip())
                        self.get_plugin("HTTPPlugin").send(line.strip())
                        self.get_plugin("RedisPubSubPlugin").send(line.strip())
                        self.get_plugin("FileBasedPlugin").send(line.strip())
        except Exception as e:
            self.logger.error(f"Error reading the log file: {e}")

    def on_stop(self):
        """
        Log the agent's shutdown.
        """
        self.logger.info("LogMonitorAgent stopped.")


if __name__ == "__main__":
    orchestrator = Orchestrator()

    # register agents
    fw_agent: AgentEntry = orchestrator.register_agent(
        LogMonitorAgent, "LogMonitorAgent"
    )

    # start all agents
    orchestrator.start()

    # wait for all agents to complete
    orchestrator.join()
```

In this example, the `LogMonitorAgent` registers four communication plugins: `ZeroMQPlugin`, `HTTPPlugin`, `RedisPubSubPlugin`, and `FileBasedPlugin`. During execution, the agent sends log messages using these plugins.

* * *

## Conclusion

The PyOrchestrate framework provides a powerful and flexible way to manage multi-process and multi-thread architectures. With the addition of the plugin system, it is now even easier to extend agent functionalities dynamically. Whether you need to add communication capabilities, logging, or other features, the plugin system makes it simple and efficient.

For more information and detailed documentation, please refer to the repository and the `docs` directory.
