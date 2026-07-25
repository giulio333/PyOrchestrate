## LoopingAgent

The **LoopingAgent** is a specialized agent designed for continuous execution. It repeatedly runs its logic in a loop until explicitly stopped or a condition is met.

### Key Features:

-   Infinite or conditional looping logic.
-   Ideal for daemon-like tasks.
-   Provides hooks for custom start and stop conditions.

### Use Case:

Monitoring a directory for file changes or running a custom server that operates indefinitely.

### Example:

```python
from pyorchestrate import LoopingAgent

class FileMonitorAgent(LoopingAgent):
    def runner(self):
        print("Monitoring files...")
```
