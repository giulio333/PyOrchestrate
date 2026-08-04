"""End-to-end test for the reporting of an agent configuration error.

An agent whose configuration does not validate aborts inside `BaseAgent.run()`,
before `setup()` and `execute()`. That failure must be visible to the
orchestrator the same way any other agent error is: as an `agent_error` record
in the event store and as an `AGENT_ERROR` callback.
"""

import time

import pytest

from PyOrchestrate.core.agent import BaseThreadAgent
from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator, RunMode
from PyOrchestrate.core.utilities.event import OrchestratorEvent
from PyOrchestrate.core.utilities.validation import ValidationResult, ValidationSeverity


class MisconfiguredWorker(BaseThreadAgent):
    """Its configuration never validates, so execution never begins."""

    class Config(BaseThreadAgent.Config):
        threshold: int = -1

        def validate(self):
            results = super().validate()
            results.append(
                ValidationResult(
                    field="threshold",
                    message="threshold must be positive",
                    severity=ValidationSeverity.ERROR,
                )
            )
            return results

    config: Config

    def execute(self):
        raise AssertionError("execute() must not run with an invalid configuration")


@pytest.fixture
def orchestrator():
    result = Orchestrator(
        config=Orchestrator.Config(
            run_mode=RunMode.DAEMON,
            enable_command_interface=False,
            check_interval=0.05,
        ),
        name="config_error_orchestrator",
    )
    yield result
    # Agents first, then the router, in the order join() uses: a handler left
    # polling after the test keeps a daemon thread on a channel that only the
    # interpreter shutdown closes.
    result.worker_pool.shutdown_all(timeout=2.0)
    result.message_router.stop()


def wait_for(predicate, timeout: float = 5.0):
    """Poll until the predicate holds, since routing is asynchronous."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_config_error_is_recorded_in_event_history(orchestrator):
    orchestrator.register_agent(MisconfiguredWorker, "misconfigured")
    orchestrator.start()

    def error_recorded():
        return orchestrator.event_bus.get_history(event_type="agent_error")

    assert wait_for(error_recorded), "no agent_error reached the event store"

    records = orchestrator.event_bus.get_history(event_type="agent_error")
    assert len(records) == 1
    assert records[0].agent == "misconfigured"
    assert records[0].severity == "ERROR"
    assert "threshold" in records[0].data["error_message"]


def test_config_error_invokes_the_registered_callback(orchestrator):
    seen = []
    orchestrator.register_event(
        OrchestratorEvent.AGENT_ERROR,
        lambda agent_name, error_message: seen.append((agent_name, error_message)),
    )
    orchestrator.register_agent(MisconfiguredWorker, "misconfigured")
    orchestrator.start()

    assert wait_for(lambda: seen), "AGENT_ERROR callback was never invoked"
    assert seen[0][0] == "misconfigured"
    assert "threshold" in seen[0][1]
