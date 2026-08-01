"""Command handler tests against a real orchestrator.

A MagicMock orchestrator answers any attribute, which is exactly how the
handlers kept reading the removed `orchestrator.dependencies` unnoticed. These
tests therefore use a real instance.
"""

import os
import time

import pytest

from PyOrchestrate.core.agent import BaseThreadAgent
from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator, RunMode
from PyOrchestrate.core.utilities.command_handler import CommandHandler


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


def test_agent_status_reports_dependencies_and_lifecycle_state(handler):
    result = handler.execute_command("status", ["consumer"])

    assert result["name"] == "consumer"
    assert result["dependencies"] == ["producer"]
    assert result["lifecycle_state"] == "registered"
    assert result["alive"] is False


def test_agent_status_reports_no_dependencies_for_an_independent_agent(handler):
    result = handler.execute_command("status", ["producer"])

    assert result["dependencies"] == []


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
