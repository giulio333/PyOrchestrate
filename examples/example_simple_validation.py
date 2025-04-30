#!/usr/bin/env python3
"""
Esempio semplice di validazione personalizzata e utilizzo di Orchestrator.
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
    """Agente minimale che si limita a loggare il valore di threshold."""

    class Config(BaseClassConfig):
        """Configurazione con un solo campo custom e validazione semplice."""

        threshold: int = 10
        validation_policy = ValidationPolicy()

        def _validate(self) -> List[ValidationResult]:
            results = super()._validate()
            if self.threshold < 0 or self.threshold > 30:
                results.append(
                    ValidationResult(
                        field="threshold",
                        is_valid=False,
                        message="Threshold deve essere tra 0 e 30.",
                        severity=ValidationSeverity.WARNING,
                    )
                )
            return results

    config: Config

    def execute(self):
        super().execute()

        for _ in range(self.config.threshold):
            self.logger.info(f"Threshold corrente: {self.config.threshold}")


if __name__ == "__main__":

    orchestrator = Orchestrator()
    orchestrator.register_agent(
        SimpleAgent, "simple_agent_invalid", SimpleAgent.Config(threshold=150)
    )
    orchestrator.start()
    orchestrator.join()
