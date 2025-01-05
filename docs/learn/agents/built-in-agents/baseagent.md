## BaseAgent

The **BaseAgent** is the foundation of all other agents in PyOrchestrate. It provides the basic structure for any custom agent. Use it as a starting point to create your own agents with completely custom behavior.


### Key Features:

#### run Method

This is the entry point for all agents, encapsulating their entire lifecycle and handling the low-level execution logic.

In essence, the `run()` method in BaseAgent overrides the run method from `threading.Thread` or `multiprocessing.Process`.

It begins by recording the **start time** and setting up the **logger** to track operations. Next, it **validates the configuration**, performs the initial **setup**, and signals readiness through the **ready_event**. The main logic of the agent will be defined in the execute method, which must be implemented in derived classes. Any errors during execution are caught and logged. Finally, the agent signals completion by setting the close_event and logs the total execution time. This structured flow ensures robustness and consistency across all agents.

``` mermaid
sequenceDiagram
    autonumber
    participant BaseAgent
    participant BaseAgent.Config
    participant BaseAgent.StateEvents
    participant BaseAgent.ControlEvents

    BaseAgent->>BaseAgent: Setup Logger
    BaseAgent->>BaseAgent.Config: Validate Configuration
    break Validation Failed
        BaseAgent.Config-->>BaseAgent: Raise ValidationError
    end
    BaseAgent->>BaseAgent.ControlEvents: Wait for setup_event
    BaseAgent->>BaseAgent: setup()
    BaseAgent->>BaseAgent.StateEvents: Set ready_event
    BaseAgent->>BaseAgent.ControlEvents: Wait for execute_event
    BaseAgent->>BaseAgent: execute()
    break If Exception Occurs
        BaseAgent->>BaseAgent: Log Exception
    end
    BaseAgent->>BaseAgent.StateEvents: Set close_event
```

::: tip
The `execute()` method is abstract and must be overridden in all derived classes.
:::

::: tip
The `setup()` method is abstract and must be overridden in all derived classes.
:::

::: warning
The `run()` method orchestrates the entire lifecycle of the agent, from `setup` to `shutdown`.

Marked as `@final` to prevent overriding in derived class ensuring that the core logic remains consistent across all agents.
:::


### Use Case:

When no predefined agent meets your requirements, the `BaseAgent` is ideal for implementing custom logic.
