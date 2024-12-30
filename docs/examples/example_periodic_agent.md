---
title: Periodic Agent
---

Here is an example of a simple `PeriodicAgent` of type `ProcessAgent` that makes some work periodically.

First, import the necessary classes. We will need `PeriodicAgent` and `ProcessAgent`:

``` python
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.base.periodic_agent import PeriodicAgent
from PyOrchestrate.core.base.base_agent import ProcessAgent
```

Then, create a class that inherits from `PeriodicAgent` and `ProcessAgent`:

``` python
class FileWriter(PeriodicAgent["FileWriter.Config"], ProcessAgent["FileWriter.Config"]):
    """Agent Class that writes to a file periodically."""
    
    class Config(PeriodicAgent.Config):
        """Agent Configuration class."""

        limit = 5
        execution_interval = 1
        output_directory = "output"

    def setup(self):
        """
        Setup method for the agent.
        """
        super().setup()

        self.logger.info(f"FileWriter {self.name} inizializzato.")

    def runner(self):
        """
        Runner method for the agent.
        """
        self.logger.debug("Doing some work")
```

In this example, we have defined a `FileWriter` class that inherits from `PeriodicAgent` and `ProcessAgent`. 
The `Config` class is used to define the configuration of the agent. The `setup` method is used to initialize the agent, 
and the `runner` method is used to define the work that the agent will do periodically.

No imagine that in our application we want to create two instances of the `FileWriter`.

!!! tip "Config"
    All **Agent** classes have a `Config` class that define must-have configuration parameters for that specific agent.
    In this case, our `PeriodicAgent` must have the `execution_interval` and `limit` parameters.
     
    Defining a `Config` class is our `FileWriter` class, we are overriding the default configuration of the 
    `PeriodicAgent` with custom values.
    
    We are also defining a new parameter `output_directory` that is specific to our `FileWriter` agent.
    
What about their configuration? Both agents will have the same configuration (all `FileWriter` instances will have the 
same `Config` class). But what if we want to have different configurations for each agent?

We can create a custom `Config` object simply by creating a new instance of the `Config` class and passing the desired
values to override the default ones and pass it to the `register_agent` method.



``` python
if __name__ == "__main__":
    orchestrator = Orchestrator("CoolOrchestrator")

    # register agents
    orchestrator.register_agent(FileWriter, "FileWriter1")

    # second agent with custom configuration
    custom_config = FileWriter.Config(execution_interval=.1, limit=40)
    orchestrator.register_agent(FileWriter, "FileWriter2", custom_config)

    # start all agents
    orchestrator.start()
    
    # wait for all agents to complete
    orchestrator.join()
```

As you can se, the first agent will have the default configuration, while the second agent will have a custom one.
So the first agent will log a message every second for 5 times, while the second agent will write to the file every
100ms for 40 times.

## Full Example

Remember that a good practice is to put the agent class in a `models.py` file and the main code in a `main.py` file.

``` python
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.base.periodic_agent import PeriodicAgent
from PyOrchestrate.core.base.base_agent import ProcessAgent


class FileWriter(PeriodicAgent["FileWriter.Config"], ProcessAgent["FileWriter.Config"]):
    """Agent Class that writes to a file periodically."""

    class Config(PeriodicAgent.Config):
        """Agent Configuration class."""

        limit = 5
        execution_interval = 1
        output_directory = "output"

    def setup(self):
        """
        Setup method for the agent.
        """
        super().setup()

        self.logger.info(f"FileWriter {self.name} inizializzato.")

    def runner(self):
        """
        Runner method for the agent.
        """
        self.logger.debug("Doing some work")


if __name__ == "__main__":
    orchestrator = Orchestrator("CoolOrchestrator")

    # register agents
    orchestrator.register_agent(FileWriter, "FileWriter1")

    # second agent with custom configuration
    custom_config = FileWriter.Config(execution_interval=.1, limit=40)
    orchestrator.register_agent(FileWriter, "FileWriter2", custom_config)

    # start all agents
    orchestrator.start()

    # wait for all agents to complete
    orchestrator.join()
```