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

            message = ServiceMessage(
                self.name,
                "info",
                payload={"message": "test message."},
                timestamp=datetime.fromtimestamp(time.time()),
            )
            self.send_message(message)


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
