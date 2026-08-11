"""Command handler tests against a real orchestrator.

A MagicMock orchestrator answers any attribute, which is exactly how the
handlers kept reading the removed `orchestrator.dependencies` unnoticed. These
tests therefore use a real instance.
"""

import json
import os
import time

import pytest

from PyOrchestrate.core.agent import BaseThreadAgent
from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator, RunMode
from PyOrchestrate.core.utilities.command_handler import (
    CommandException,
    CommandHandler,
)
from PyOrchestrate.core.utilities.event import OrchestratorEvent


class Worker(BaseThreadAgent):
    def execute(self) -> None:
        super().execute()


@pytest.fixture
def handler():
    orchestrator = Orchestrator(
        config=Orchestrator.Config(
            run_mode=RunMode.STOP_ON_EMPTY,
            enable_command_interface=False,
        ),
        name="command_orchestrator",
    )
    orchestrator.register_agent(Worker, "consumer")
    orchestrator.register_agent(Worker, "producer")
    orchestrator.add_dependency("consumer", ["producer"])
    return CommandHandler(orchestrator)


def test_dependencies_command_reads_the_dependency_graph(handler):
    result = handler.execute_command("dependencies", [])

    assert result == {"dependencies": {"consumer": ["producer"]}}


def test_dependencies_command_still_omits_independent_agents_after_start(handler):
    """Starting the orchestrator used to add `"producer": []` to the payload."""
    handler.orchestrator.start()

    result = handler.execute_command("dependencies", [])

    assert result == {"dependencies": {"consumer": ["producer"]}}


def test_agent_status_reports_dependencies_and_lifecycle_state(handler):
    result = handler.execute_command("status", ["consumer"])

    assert result["name"] == "consumer"
    assert result["dependencies"] == ["producer"]
    assert result["lifecycle_state"] == "registered"
    assert result["alive"] is False


def test_agent_status_reports_no_dependencies_for_an_independent_agent(handler):
    result = handler.execute_command("status", ["producer"])

    assert result["dependencies"] == []


def test_agent_status_reports_an_unknown_agent_as_not_found(handler):
    """The 404 used to be re-wrapped as `500 Failed to get status for ...`."""
    with pytest.raises(CommandException) as error:
        handler.execute_command("status", ["ghost"])

    assert error.value.code == 404
    assert str(error.value) == "Agent ghost not found"


def test_every_agent_command_reports_an_unknown_agent_with_the_same_code(handler):
    codes = {}
    for command in ("status", "start", "stop"):
        with pytest.raises(CommandException) as error:
            handler.execute_command(command, ["ghost"])
        codes[command] = error.value.code

    assert codes == {"status": 404, "start": 404, "stop": 404}


def test_ps_reports_lifecycle_state_for_registered_agents(handler):
    result = handler.execute_command("ps", [])

    states = {
        agent["agent_name"]: agent["lifecycle_state"] for agent in result["agents"]
    }
    assert states == {"consumer": "registered", "producer": "registered"}


def test_stats_reuses_the_same_process_handle_across_calls(handler):
    pid = os.getpid()

    assert handler._process_for(pid) is handler._process_for(pid)


def test_a_reused_process_handle_measures_cpu_usage(handler):
    pid = os.getpid()
    handler._process_for(pid).cpu_percent()  # first call only sets the baseline

    deadline = time.monotonic() + 0.2
    while time.monotonic() < deadline:  # burn measurable cpu time
        pass

    assert handler._process_for(pid).cpu_percent() > 0


def test_stats_forgets_the_processes_of_agents_that_are_gone(handler):
    handler._process_for(os.getpid())

    handler.execute_command("stats", [])

    assert handler._process_cache == {}


def test_history_with_last_zero_returns_no_events(handler):
    """`--last 0` used to answer with the whole ring buffer."""
    assert handler.execute_command("history", [])["count"] > 0

    result = handler.execute_command("history", [json.dumps({"last": 0})])

    assert result["count"] == 0
    assert result["events"] == []


def test_history_with_a_negative_last_returns_no_events(handler):
    result = handler.execute_command("history", [json.dumps({"last": -5})])

    assert result["count"] == 0


def test_history_stats_count_the_events_kept_in_the_heartbeat_store(handler):
    """Heartbeats are routed to a BucketRingStore and used to be uncounted."""
    for _ in range(3):
        handler.orchestrator.event_bus.emit(
            OrchestratorEvent.AGENT_HEARTBEAT, agent_name="consumer"
        )

    by_type = handler.execute_command("history-stats", [])["statistics"]["by_type"]

    assert by_type[OrchestratorEvent.AGENT_HEARTBEAT.value] == 3
    assert by_type[OrchestratorEvent.AGENT_REGISTERED.value] == 2
