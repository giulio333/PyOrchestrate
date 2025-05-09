---
title: Validation and Orchestrator
---

# Custom Validation and Orchestrator Example

This advanced example demonstrates how to implement custom validation for agent configurations and how to use the Orchestrator to manage multiple agents with different validation states.

## Overview

In PyOrchestrate, validation is an important mechanism that helps ensure your agents are properly configured before they start. This example shows how to:

1. Create a simple agent with custom validation rules
2. Define validation policies to handle warnings and errors
3. Use the Orchestrator to manage multiple agents with different validation states
4. Handle validation errors appropriately

## Agent Implementation

Let's create a `SimpleAgent` that includes custom configuration validation:

```python
from typing import List
from PyOrchestrate.core.utilities.validation import (
    ValidationResult,
    ValidationSeverity,
    ValidationPolicy,
)
from PyOrchestrate.core.base.base import BaseClassConfig
from PyOrchestrate.core.agent.base_agent import BaseProcessAgent


class SimpleAgent(BaseProcessAgent):
    """Minimal agent that only logs the threshold value."""

    class Config(BaseClassConfig):
        """Configuration with a single custom field and simple validation."""

        threshold: int = 10
        debug: bool = True
        validation_policy = ValidationPolicy(ignore_warnings=True, ignore_errors=False)

        def validate(self) -> List[ValidationResult]:
            results = super().validate()
            
            # Add custom validation for threshold
            if self.threshold < 0 or self.threshold > 30:
                results.append(
                    ValidationResult(
                        field="threshold",
                        message="Threshold must be between 0 and 30.",
                        severity=ValidationSeverity.ERROR,
                    )
                )
                
            # Add warning for debug mode
            if self.debug:
                results.append(
                    ValidationResult(
                        field="debug",
                        message="Debug mode is enabled.",
                        severity=ValidationSeverity.WARNING,
                    )
                )
                
            return results

    config: Config

    def execute(self):
        super().execute()

        for _ in range(self.config.threshold):
            self.logger.info(f"Current threshold: {self.config.threshold}")
```

This agent has a simple configuration with two parameters:
- `threshold`: An integer that must be between 0 and 30
- `debug`: A boolean that triggers a warning when set to `True`

## Using Validation in Orchestrator

Once we have our agent with custom validation, we can use the Orchestrator to manage multiple instances:

```python
from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator

def run_validation_example():
    """
    Create and run multiple SimpleAgent instances with different validation states
    using the Orchestrator.
    """
    # Create an orchestrator
    orchestrator = Orchestrator()
    
    # Register an agent that will fail validation (ERROR)
    orchestrator.register_agent(
        SimpleAgent,
        "simple_agent_error",
        SimpleAgent.Config(threshold=150, debug=True),
    )
    
    # Register an agent that will have warnings but run (WARNING)
    orchestrator.register_agent(
        SimpleAgent,
        "simple_agent_warning",
        SimpleAgent.Config(threshold=10, debug=True),
    )
    
    # Register an agent with valid configuration (OK)
    orchestrator.register_agent(
        SimpleAgent,
        "simple_agent_ok",
        SimpleAgent.Config(threshold=10, debug=False),
    )
    
    # Start all agents (those that pass validation)
    orchestrator.start()
    
    # Wait for all agents to complete
    orchestrator.join()


if __name__ == "__main__":
    run_validation_example()
```

## How Validation Works in PyOrchestrate

PyOrchestrate's validation mechanism is designed to prevent runtime errors by checking configurations before agents start:

1. **Validation Process:** When you register an agent with the Orchestrator, the agent's configuration is automatically validated using its `validate()` method.

2. **Validation Results:** Each validation check produces a `ValidationResult` with:
   - `field`: The configuration field being validated
   - `message`: A descriptive message about the validation result
   - `severity`: Either `WARNING` or `ERROR`

3. **Validation Policy:** The `ValidationPolicy` determines how validation results are handled:
   - `ignore_warnings`: When `True`, warnings are logged but don't prevent the agent from starting
   - `ignore_errors`: When `False` (default), errors prevent the agent from starting

4. **Orchestrator Behavior:** 
   - Agents with validation errors will not be started (unless `ignore_errors=True`)
   - Agents with only warnings will start if `ignore_warnings=True`
   - The Orchestrator logs all validation issues for troubleshooting

## Complete Example

Here's the complete code example with imports and main execution:

```python
#!/usr/bin/env python3
"""
Simple example of custom validation and usage of Orchestrator.
"""
from typing import List
from datetime import datetime
import time
from PyOrchestrate.core.utilities.validation import (
    ValidationResult,
    ValidationSeverity,
    ValidationPolicy,
)
from PyOrchestrate.core.base.base import BaseClassConfig
from PyOrchestrate.core.agent.base_agent import BaseProcessAgent, ServiceMessage
from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator


class SimpleAgent(BaseProcessAgent):
    """Minimal agent that only logs the threshold value."""

    class Config(BaseClassConfig):
        """Configuration with a single custom field and simple validation."""

        threshold: int = 10
        debug: bool = True
        validation_policy = ValidationPolicy(ignore_warnings=True, ignore_errors=False)

        def validate(self) -> List[ValidationResult]:
            results = super().validate()
            if self.threshold < 0 or self.threshold > 30:
                results.append(
                    ValidationResult(
                        field="threshold",
                        message="Threshold must be between 0 and 30.",
                        severity=ValidationSeverity.ERROR,
                    )
                )
            if self.debug:
                results.append(
                    ValidationResult(
                        field="debug",
                        message="Debug mode is enabled.",
                        severity=ValidationSeverity.WARNING,
                    )
                )
            return results

    config: Config

    def execute(self):
        super().execute()

        for _ in range(self.config.threshold):
            self.logger.info(f"Current threshold: {self.config.threshold}")


if __name__ == "__main__":

    orchestrator = Orchestrator()
    orchestrator.register_agent(
        SimpleAgent,
        "simple_agent_error",
        SimpleAgent.Config(threshold=150, debug=True),
    )
    orchestrator.register_agent(
        SimpleAgent,
        "simple_agent_warning",
        SimpleAgent.Config(threshold=10, debug=True),
    )
    orchestrator.register_agent(
        SimpleAgent,
        "simple_agent_ok",
        SimpleAgent.Config(threshold=10, debug=False),
    )
    orchestrator.start()
    orchestrator.join()
```
