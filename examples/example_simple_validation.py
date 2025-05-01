#!/usr/bin/env python3
"""
Simple example of custom validation and usage of Orchestrator.
"""
from typing import List

from PyOrchestrate.core.utilities.validation import (
    ValidationResult,
    ValidationSeverity,
    ValidationPolicy,
)
from PyOrchestrate.core.base.base import BaseClassConfig
from PyOrchestrate.core.agent.base_agent import BaseProcessAgent
from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator


class SimpleAgent(BaseProcessAgent):
    """Minimal agent that only logs the threshold value."""

    class Config(BaseClassConfig):
        """Configuration with a single custom field and simple validation."""

        threshold: int = 10
        validation_policy = ValidationPolicy(ignore_warnings=False, ignore_errors=False)

        def validate(self) -> List[ValidationResult]:
            results = super().validate()
            if self.threshold < 0 or self.threshold > 30:
                results.append(
                    ValidationResult(
                        field="threshold",
                        is_valid=False,
                        message="Threshold must be between 0 and 30.",
                        severity=ValidationSeverity.ERROR,
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
        SimpleAgent, "simple_agent_invalid", SimpleAgent.Config(threshold=150)
    )
    orchestrator.start()
    orchestrator.join()
