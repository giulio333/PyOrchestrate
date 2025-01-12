---
title: Orchestrator in Detail
---

The Orchestrator is the central component of PyOrchestrate, designed to coordinate and supervise agents operating as 
processes or threads. 

Its structure is built to efficiently manage the complexities of a multi-process and multi-thread 
architecture, providing advanced features for dependency management, lifecycle control, and monitoring.
* * *

## Registering Agents

One of the first steps in using the **Orchestrator** is **registering agents**.

What does it mean to register an agent? You are telling the Orchestrator to create a new agent instance from a specific
class.

```python
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.orchestrator.memory import AgentEntry
from models import MyAgent

orchestrator = Orchestrator("MyOrchestrator")
fw_agent1: AgentEntry = orchestrator.register_agent(MyAgent, "MyAgent1")
fw_agent2: AgentEntry = orchestrator.register_agent(MyAgent, "MyAgent2")
fw_agent3: AgentEntry = orchestrator.register_agent(MyAgent, "MyAgent3")
``` 

So you can create many agents from the same class and give them a unique name. All these agents will be the same, but
each one will have its own lifecycle and state.

!!! tip "Agent and AgentEntry"
    In the above example you can see that the `register_agent` method returns an `AgentEntry` object instead of the
    agent **instance**.
    
    This object contains all the metadata and configuration required to create and manage the agent during execution.
    An important data stored in the `AgentEntry` is the agent's **instance**.

What if you want to create multiple agents from the same class but with different configurations?
        
This method allows to pass a custom configuration object to the agent during registration.

```python
from PyOrchestrate.core.orchestrator import Orchestrator
from models import MyAgent # type: ignore

orchestrator = Orchestrator("MyOrchestrator")
custom_config2 = MyAgent.Config(execution_interval=2)
custom_config3 = MyAgent.Config(execution_interval=3)

orchestrator.register_agent(MyAgent, "MyAgent1")
orchestrator.register_agent(MyAgent, "MyAgent2", custom_config=custom_config2)
orchestrator.register_agent(MyAgent, "MyAgent3", custom_config=custom_config3)
```

If not specified, all agents made from the same class will share the same configuration object. If a different
configuration is needed, it can be passed as a parameter to the `register_agent` method.

``` mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant OMemory

    User->>Orchestrator: register_agent(class, name, config)
    Orchestrator->>OMemory: add_agent(class, name, config)
    OMemory-->>OMemory: initialize_agent()
    OMemory-->>Orchestrator: Return AgentEntry
    Orchestrator-->>User: Return AgentEntr
```

        
??? Abstract "See More"
    ::: PyOrchestrate.core.orchestrator.Orchestrator.register_agent
        options:
            heading_level: 0

### Agent Memory

The Orchestrator uses a centralized memory structure, `OMemory`, to manage agents. Each agent is represented by an `AgentEntry` object, which contains:

-   **Agent Class**: The Python class defining the agent's behavior.
-   **Agent Name**: A unique identifier.
-   **Configuration**: A configuration object for the agent.
-   **Control Events**: A list of events that can be sent to the agent (e.g., setup, execute, stop).
-   **State Events**: A list of events emitted by the agent (e.g., ready, close).
            
The `OMemory` allows for quick access to registered agents and facilitates operations such as state updates or removal.

#### Add Agent

As we saw before, the `register_agent` method adds a new agent to the memory structure.

More in depth, the `OMemory` class provides the `add_agent` method to insert a new agent into the memory structure.
Let's see all operations that are performed when adding an agent:

1. Check if the agent type is Thread or Process.
2. Create a set of `ControlEvent` and `StateEvent` objects.
3. Create an `AgentEntry` object with all the metadata.
4. Add the `AgentEntry` object to the memory structure.

It is worth spending a few words on `ControlEvents` and `StateEvents`. These objects are used to manage the communication
between the Orchestrator and the agents (we will see more about this in future sections).

- **ControlEvents**: Represents an event that can be sent to an agent to control its behavior.
- **StateEvents**: Represents an event emitted by an agent to signal its state.

So, when an agent is added to the memory, events are created by Orchestrator and shared with the agent. This mechanism
allows the Orchestrator to control the agent's lifecycle and monitor its state.

Not only that, user can use these events to create relationships between agents. For example, an agent can be set to 
wait for another agent to emit a specific event before proceeding.

!!! warning "Default Events Set"
    By default, each `ControlEvent` is set to true. This means that all agents will go through all the lifecycle phases.
    If a specific agent should wait that a specific event is emitted before proceeding, the event can be set to false.
    

??? Abstract "See More"
    ::: PyOrchestrate.core.orchestrator.memory.OMemory.add_agent
        options:
            heading_level: 0
            
## Dependency Management

The Orchestrator supports defining dependencies between agents, allowing specification of which agents must run before 
others. 

Dependencies are represented as a directed acyclic graph (DAG), implemented using a dictionary mapping each 
agent to the names of the agents it depends on.

### Dependency Validation

A validation system analyzes the dependency graph to detect cycles. If a cycle is found, the Orchestrator raises an exception and halts execution.

### Topological Sorting

To ensure agents are started in the correct order, the Orchestrator performs a topological sort of the dependency graph using a Breadth-First Search (BFS) algorithm. This process:

1.  Calculates the in-degrees of each node.
2.  Uses a queue to process nodes with zero in-degree.
3.  Orders agents based on dependency, ensuring each agent is executed only after its predecessors.

## Starting Agents

When the start method is invoked, the Orchestrator:

1.  Validates dependencies to prevent errors.
2.  Orders agents topologically.
3.  Starts agents sequentially, respecting the established order.
4.  Emits events signaling the start of each agent's execution.

So after ensure that all dependencies are satisfied, the Orchestrator starts the agents in the correct order.

Only at this point, the **agent instances are created** in memory. This is done thanks to `AgentEntry` data stored during
the [registration phase](#registering-agents).

??? Abstract "See More"
    ::: PyOrchestrate.core.orchestrator.Orchestrator.start
        options:
            heading_level: 0


## Monitoring and Joining

The Orchestrator continuously monitors agent states using the `join` method, which waits for all agents to complete. During this phase:

-   Agent states are updated in real-time.
-   Specific events (e.g., agent termination) are emitted via an `EventManager`.
-   A final event signals the completion of all agents.

## Stopping Agents

When requested, the Orchestrator invokes the stop method on each agent, gracefully terminating their operations and ensuring resource deallocation.

* * *

## Event Emission

The Orchestrator uses an `EventManager` to emit signals during various lifecycle phases of agents. For example:

-   **Agent Start**: Emits an `AGENT_STARTED` event.
-   **Agent Termination**: Emits an `AGENT_TERMINATED` event.
-   **All Agents Completed**: Emits an `ALL_AGENTS_COMPLETED` event.

This event system enables asynchronous communication between the Orchestrator and other system components.

## Error Handling

The Orchestrator is designed to be resilient. If an agent encounters an error, the Orchestrator:

1.  Logs the error.
2.  Updates the agent's state in memory.
3.  Decides whether to continue executing other agents or halt the system, based on configuration.

* * *

## Conclusion

The Orchestrator is a flexible and robust component designed to simplify the management of complex multi-process and 
multi-thread systems. Its modular structure and use of advanced mechanisms like dependency management, continuous 
monitoring, and event emission make it a powerful tool for developers seeking scalable and efficient solutions.

## Simple Join Method

The `Orchestrator` class includes a simple `join` method that joins all processes or threads managed by the orchestrator. This method waits for all the agents to complete their execution.

### Usage

```python
from PyOrchestrate.core.orchestrator import Orchestrator

orchestrator = Orchestrator("MyOrchestrator")
# Register agents
orchestrator.start()
orchestrator.join()
```

## Complex Join Method

The `Orchestrator` class also includes a more complex `join` method that not only joins the processes or threads but also checks the status of each agent before and after joining. This method logs the status of each agent and ensures that all agents have completed successfully.

### Usage

```python
from PyOrchestrate.core.orchestrator import Orchestrator

orchestrator = Orchestrator("MyOrchestrator")
# Register agents
orchestrator.start()
orchestrator.complex_join()
```
