"""End-to-end tests for the orchestrator shutdown path.

The CLI 'shutdown' command only sets `_shutdown_requested`. These tests run real
agents to verify that leaving the join() loop actually terminates them before
channels and plugins are torn down.
"""

import threading
import time

import pytest

from PyOrchestrate.core.agent import BaseProcessAgent, LoopingThreadAgent
from PyOrchestrate.core.orchestrator.memory import AgentLifecycleState
from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator, RunMode
from PyOrchestrate.core.utilities.command_handler import CommandHandler


class CooperativeWorker(LoopingThreadAgent):
    """Loops forever until the cooperative stop event is set."""

    def cycle(self) -> None:
        time.sleep(0.01)


class StubbornProcessWorker(BaseProcessAgent):
    """Ignores the stop event, so only force-termination can end it."""

    def execute(self) -> None:
        while True:
            time.sleep(0.05)


@pytest.fixture
def orchestrator():
    result = Orchestrator(
        config=Orchestrator.Config(
            run_mode=RunMode.DAEMON,
            enable_command_interface=False,
            check_interval=0.05,
            agent_stop_timeout=3.0,
        ),
        name="shutdown_orchestrator",
    )
    yield result
    result.worker_pool.shutdown_all(timeout=2.0)


def request_shutdown_when_alive(orchestrator, entry) -> threading.Thread:
    """Set the shutdown flag exactly like the CLI handler does, once running."""

    def run():
        deadline = time.monotonic() + 5
        while not entry.is_alive() and time.monotonic() < deadline:
            time.sleep(0.01)
        orchestrator._shutdown_requested = True

    thread = threading.Thread(target=run)
    thread.start()
    return thread


def test_daemon_shutdown_terminates_cooperative_agent(orchestrator):
    entry = orchestrator.register_agent(CooperativeWorker, "cooperative")
    orchestrator.start()
    requester = request_shutdown_when_alive(orchestrator, entry)

    orchestrator.join()
    requester.join(timeout=1)

    assert not entry.is_alive()
    assert entry.state is AgentLifecycleState.TERMINATED
    assert orchestrator.worker_pool.all_finished


def test_daemon_shutdown_force_terminates_stubborn_process_agent(orchestrator):
    orchestrator.config.agent_stop_timeout = 0.5
    entry = orchestrator.register_agent(StubbornProcessWorker, "stubborn")
    orchestrator.start()
    requester = request_shutdown_when_alive(orchestrator, entry)

    orchestrator.join()
    requester.join(timeout=1)

    assert not entry.is_alive()
    assert entry.state is AgentLifecycleState.TERMINATED


def test_cli_shutdown_command_terminates_agents(orchestrator):
    entry = orchestrator.register_agent(CooperativeWorker, "cli-stopped")
    handler = CommandHandler(orchestrator)
    orchestrator.start()

    deadline = time.monotonic() + 5
    while not entry.is_alive() and time.monotonic() < deadline:
        time.sleep(0.01)

    joined = threading.Thread(target=orchestrator.join)
    joined.start()
    handler.execute_command("shutdown", [])
    joined.join(timeout=10)

    assert not joined.is_alive()
    assert not entry.is_alive()
    assert entry.state is AgentLifecycleState.TERMINATED
