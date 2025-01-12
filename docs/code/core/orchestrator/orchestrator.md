::: PyOrchestrate.core.orchestrator.orchestrator

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
