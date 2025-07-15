
# Communication Plugins

Communication plugins in PyOrchestrate allow agents to interact with other agents, external systems, and more.

## Using Communication Plugins: Automatic vs Manual Management

PyOrchestrate provides two main ways to use communication plugins in your agents:

### 1. Automatic Initialization/Finalization (Recommended)

By defining your plugins inside the `Plugin` inner class of your agent, PyOrchestrate will automatically handle their initialization and finalization during the agent's lifecycle. This is the recommended approach for most use cases.

**Example:**

```python
from PyOrchestrate.core.agent import BaseProcessAgent
from PyOrchestrate.core.plugins import ZeroMQPubSub
import zmq

class MyAgent(BaseProcessAgent):
    class Plugin(BaseProcessAgent.Plugin):
        zmq = ZeroMQPubSub("tcp://localhost:5555", zmq.PUB)

    plugin: Plugin

    def execute(self):
        super().execute()
        self.plugin.zmq.send("Hello, World!".encode())
```

---

### 2. Manual Initialization/Finalization

Alternatively, you can instantiate plugins directly in your agent (outside the `Plugin` class). In this case, you are responsible for manually initializing and finalizing the plugin.

**Example:**

```python
from PyOrchestrate.core.agent import BaseProcessAgent
from PyOrchestrate.core.plugins import ZeroMQPubSub
import zmq

class MyAgent(BaseProcessAgent):
    def __init__(self):
        super().__init__()
        self.zmq = ZeroMQPubSub("tcp://localhost:5555", zmq.PUB)
        self.zmq.initialize()  # Manual initialization

    def execute(self):
        super().execute()
        self.zmq.send("Hello, World!".encode())

    def on_close(self):
        super().finalize()
        self.zmq.finalize()  # Manual finalization
```

**Notes:**
- You must call `initialize()` on the plugin before using it.
- You must call `finalize()` on the plugin when the agent is shutting down.
- Resource management is your responsibility.

---

::: tip
Automatic management via the `Plugin` class is recommended for most scenarios. Manual management is useful for advanced or custom setups where you need more control over plugin lifecycle.
:::
