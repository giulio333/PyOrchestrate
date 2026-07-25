# PyOrchestrate Framework

[![PyOrchestrate Test](https://github.com/giulio333/PyOrchestrate/actions/workflows/python-app.yml/badge.svg)](https://github.com/giulio333/PyOrchestrate/actions/workflows/python-app.yml)

**PyOrchestrate** is a Python framework designed to simplify the creation and management of multi-process and
multi-thread architectures. It provides a structured approach to orchestrating tasks, allowing developers to focus on
logic while the framework handles complexities like process and thread management.

## Features

- **Centralized Management**: The **Orchestrator** provides unified control over all agents
- **Flexible Execution Models**: Support for both process-based and thread-based agents
- **Multiple Agent Types**: Periodic, looping, and pool agents for different execution patterns
- **Configuration-First Design**: Inner `Config` classes with type hints and validation
- **Modern Plugin System**: Inner `Plugin` classes for extending agent capabilities
- **Inter-Agent Communication**: ZeroMQ-based communication plugins (Pair, PubSub, PushPull, ReqRep)
- **Lifecycle Management**: Automated setup, execution, and cleanup of agent resources
- **Memory Management**: Built-in dependency tracking and resource cleanup
- **Structured Logging**: Loguru-based logging with per-agent log files
- **CLI Tools**: Project scaffolding and management commands

* * *

## Quick Start

### Installation

Ensure Python 3.11+ is installed, then clone the repository and install the required dependencies:

``` bash
git clone https://github.com/giulio333/PyOrchestrate.git
cd PyOrchestrate
pip install -r requirements.txt
```

To install the `pyorchestrate` CLI command, run the following command:

``` bash
pip install .
```

* * *

## Basic Usage

### Defining an Agent

Define a custom agent by inheriting from predefined agent classes like `PeriodicAgent` or `LoopingAgent`. For example,
here's a `FileWriter` agent that logs a message periodically:

``` python
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent.periodic_agent import PeriodicProcessAgent


class FileWriter(PeriodicProcessAgent):
    """Agent Class that logs a message periodically."""

    class Config(PeriodicProcessAgent.Config):
        """Process agent configuration class."""

        limit = 5
        execution_interval = 1
        directory = "/tmp"

    config: Config

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
    orchestrator = Orchestrator()

    # register agents
    orchestrator.register_agent(FileWriter, "FileWriter")
    orchestrator.register_agent(
        FileWriter,
        "FileWriter2", 
        custom_config=FileWriter.Config(execution_interval=0.2, directory="/tmp2")
    )

    # start agent
    orchestrator.start()

    # wait for agent to complete
    orchestrator.join()
```

* * *

## Configuration

Each agent has a `Config` inner class to customize behavior:

``` python
class MyAgent(PeriodicProcessAgent):
    class Config(PeriodicProcessAgent.Config):
        execution_interval = 5.0  # every 5 seconds
        api_url: str = "https://api.example.com"
        keyword: str = "important"
    
    config: Config
```

* * *

## Agent Types

PyOrchestrate provides several specialized agent types for different use cases:

### Periodic Agents
Execute tasks at regular intervals:
- **PeriodicProcessAgent**: For CPU-intensive, isolated periodic tasks
- **PeriodicThreadAgent**: For I/O-bound periodic tasks with shared memory

### Looping Agents  
Execute tasks in continuous loops:
- **LoopingProcessAgent**: For continuous processing in isolated processes
- **LoopingThreadAgent**: For continuous processing with shared memory

### Pool Agents
Manage worker pools for parallel processing:
- **PoolProcessAgent**: Manages a pool of worker processes
- **PoolThreadAgent**: Manages a pool of worker threads

### Base Agents
Foundation classes for custom implementations:
- **BaseProcessAgent**: Base class for process-based agents
- **BaseThreadAgent**: Base class for thread-based agents

## Example Use Cases

1. **Periodic Data Collection**  
   Use `PeriodicProcessAgent` to collect sensor data every N seconds and save it to a database.

2. **Real-time Processing**  
   Use `LoopingThreadAgent` for continuous data stream processing with low latency.

3. **Batch Processing**  
   Use `PoolProcessAgent` to distribute heavy computational tasks across multiple worker processes.

4. **Event Monitoring**  
   Use `PeriodicThreadAgent` to monitor file system changes or API endpoints.

5. **Hierarchical Orchestration**  
   The main orchestrator manages agents that themselves coordinate subtasks using different agent types.

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

For more details, see the CLI documentation in [`docs/cli/`](docs/cli/index.mdx).

* * *

## Plugin System

The PyOrchestrate framework includes a plugin system that allows for dynamic extension of agent functionalities through inner `Plugin` classes. This system supports various types of plugins, including communication plugins.

### Communication Plugins

Communication plugins enable agents to send and receive messages using different communication mechanisms. The following communication plugins are available:

- **ZeroMQPair**: Provides bidirectional exclusive communication using ZeroMQ PAIR sockets
- **ZeroMQPubSub**: Provides publish-subscribe communication using ZeroMQ PUB/SUB sockets  
- **ZeroMQPushPull**: Provides load-balanced communication using ZeroMQ PUSH/PULL sockets
- **ZeroMQReqRep**: Provides request-reply communication using ZeroMQ REQ/REP sockets

### Example Usage

Here's an example of how to use the modern plugin system with an agent:

``` python
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import PeriodicProcessAgent
from PyOrchestrate.core.plugins.com import ZeroMQPair, ZeroMQPubSub
import zmq


class WeatherCollector(PeriodicProcessAgent):
    """Agent that collects weather data and sends it via ZeroMQ."""

    class Config(PeriodicProcessAgent.Config):
        api_url: str = "https://api.weather.com/data"
        execution_interval: float = 30.0  # every 30 seconds
        limit: int = 10

    class Plugin(PeriodicProcessAgent.Plugin):
        """Plugin configuration for weather collector."""
        
        publisher = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
        pair_comm = ZeroMQPair("tcp://*:5556", bind=True)

    config: Config
    plugin: Plugin

    def setup(self):
        """Setup method - plugins are automatically initialized."""
        super().setup()
        self.logger.info(f"Weather collector initialized")

    def runner(self):
        """Collect weather data and publish it."""
        super().runner()
        
        # Simulate weather data collection
        weather_data = f"Temperature: 25°C, Humidity: 60%"
        
        # Send via publisher plugin
        self.plugin.publisher.send(weather_data.encode())
        self.logger.info(f"Published: {weather_data}")
        
        # Try to receive control messages via pair plugin
        try:
            control_msg = self.plugin.pair_comm.recv(blocking=False).decode()
            self.logger.info(f"Control message received: {control_msg}")
        except:
            pass  # No control message available


class WeatherDisplay(PeriodicProcessAgent):
    """Agent that receives and displays weather data."""

    class Config(PeriodicProcessAgent.Config):
        execution_interval: float = 1.0
        limit: int = 50

    class Plugin(PeriodicProcessAgent.Plugin):
        """Plugin configuration for weather display."""
        
        subscriber = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB)

    config: Config
    plugin: Plugin

    def runner(self):
        """Listen for weather data."""
        super().runner()
        
        try:
            weather_data = self.plugin.subscriber.recv(blocking=False).decode()
            self.logger.success(f"Weather update: {weather_data}")
        except:
            self.logger.debug("No weather data available")


if __name__ == "__main__":
    orchestrator = Orchestrator()

    # Register agents
    orchestrator.register_agent(WeatherCollector, "WeatherCollector")
    orchestrator.register_agent(WeatherDisplay, "WeatherDisplay")

    # Start all agents
    orchestrator.start()

    # Wait for all agents to complete
    orchestrator.join()
```

In this example, agents use the modern `Plugin` inner class pattern. The framework automatically initializes plugins during the agent's setup phase, and you can access them directly via `self.plugin.plugin_name`.

* * *

## Modern Architecture

PyOrchestrate follows a **container orchestration** approach - think "Docker for Python processes". The framework handles the complete lifecycle of execution units (Agents) with these key principles:

### Configuration Pattern
Every agent uses the **Config inner class pattern** with type hints:
```python
class MyAgent(PeriodicProcessAgent):
    class Config(PeriodicProcessAgent.Config):
        api_url: str = "https://api.example.com"
        keyword: str = "important" 
        execution_interval: float = 5.0
    
    config: Config
```

### Plugin System
Extend agent functionality through the **Plugin inner class**:
```python
class MyAgent(PeriodicProcessAgent):
    class Plugin(PeriodicProcessAgent.Plugin):
        zmq_pub = ZeroMQPubSub("tcp://*:5555", zmq.PUB)
        zmq_pair = ZeroMQPair("tcp://*:5556", bind=True)
    
    plugin: Plugin
    
    def runner(self):
        self.plugin.zmq_pub.send(b"Hello World")
```

### Lifecycle Management
Agents follow a structured lifecycle:
1. **Setup**: Initialize resources and plugins
2. **Runner/Execute**: Core business logic execution  
3. **On Close**: Cleanup resources and connections

### Process vs Thread Selection
- **ProcessAgent**: CPU-intensive, isolated tasks with memory separation
- **ThreadAgent**: I/O-bound tasks with shared memory and faster communication

## Conclusion

The PyOrchestrate framework provides a powerful and flexible way to manage multi-process and multi-thread architectures. With the modern configuration and plugin systems, it's easier than ever to build scalable, maintainable concurrent applications in Python.

For more information and detailed documentation, see the `docs/` directory.

### Working on the documentation

The docs are a [Mintlify](https://mintlify.com) site living in `docs/`:

```bash
cd docs && npx mint dev          # anteprima locale
npx mint broken-links            # verifica dei link
./scripts/build_api_reference.sh # rigenera l'API reference dalle docstring
```

L'API reference è generata da Sphinx a partire dalle docstring dei
sorgenti: `sphinx/` contiene la configurazione, `docs/sdk-artifacts/`
l'output consumato da Mintlify.

* * *

## License

PyOrchestrate is released under the [MIT License](LICENSE).