import json
from unittest.mock import MagicMock

import pytest

from PyOrchestrate.cli import (
    ArgumentParser,
    CLIConstants,
    OrchestratorCommand,
    OutputFormatter,
    StatsCommand,
)
from PyOrchestrate.core.agent import BaseThreadAgent
from PyOrchestrate.core.orchestrator.event_store import BucketRingStore, EventStore
from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator, RunMode
from PyOrchestrate.core.utilities.command_handler import CommandHandler
from PyOrchestrate.core.utilities.messaging import ServiceMessage


class Worker(BaseThreadAgent):
    def execute(self) -> None:
        super().execute()


class StubClient:
    """Answers `stats` with a payload built by a real command handler."""

    zmq_address = "tcp://127.0.0.1:5555"

    def __init__(self, handler: CommandHandler):
        self._handler = handler

    def send_command(self, command: str, args=None) -> dict:
        return {"status": "success", "data": self._handler.execute_command(command, [])}


@pytest.fixture
def orchestrator():
    result = Orchestrator(
        config=Orchestrator.Config(
            run_mode=RunMode.STOP_ON_EMPTY,
            enable_command_interface=False,
            max_workers=5,
        ),
        name="cli_orchestrator",
    )
    result.register_agent(Worker, "worker")
    result.register_agent(Worker, "spare")

    yield result

    result.worker_pool.shutdown_all(timeout=2.0)


@pytest.fixture
def cli_response(orchestrator):
    """Answer commands the way the CLI sees them: as the response payload."""
    handler = CommandHandler(orchestrator)

    def run(command: str, args: list | None = None) -> dict:
        request = ServiceMessage.create_command(
            sender="cli", command=command, args=args or []
        )
        return handler.execute_command_msg(request).payload

    return run


@pytest.fixture
def stats_command(orchestrator):
    return StatsCommand(StubClient(CommandHandler(orchestrator)), OutputFormatter())


def test_starter_template_uses_current_command_interface_config():
    compile(CLIConstants.STARTER_TEMPLATE, "starter.py", "exec")
    assert 'command_zmq_address="tcp://*:5555"' in CLIConstants.STARTER_TEMPLATE
    assert "command_socket_path" not in CLIConstants.STARTER_TEMPLATE


def test_history_type_option_is_forwarded_as_event_name():
    parser = ArgumentParser.create_parser()
    args = parser.parse_args(["history", "--type", "AGENT_STARTED", "--last", "5"])

    ArgumentParser.prepare_command_from_args(args)

    command = OrchestratorCommand(MagicMock(), OutputFormatter())
    params = json.loads(command._prepare_command_args(args)[0])

    assert params["event_name"] == "AGENT_STARTED"
    assert params["last"] == 5


def _capacity_info_with(event_count: int, capacity: int = 100) -> dict:
    """Build a capacity payload from a real store, as the orchestrator does."""
    store = EventStore(capacity=capacity)
    for index in range(event_count):
        store.record(category="orchestrator", event_name=f"event_{index}")

    return store.get_capacity_info()


def test_history_table_formats_event_name_filter():
    output = OutputFormatter._format_history(
        {
            "events": [],
            "count": 0,
            "filters": {"event_name": "AGENT_STARTED"},
            "capacity_info": _capacity_info_with(0),
        }
    )

    assert "Filters: type=AGENT_STARTED" in output


def test_history_table_reports_default_store_usage():
    output = OutputFormatter._format_history(
        {
            "events": [],
            "count": 0,
            "filters": {},
            "capacity_info": _capacity_info_with(3),
        }
    )

    assert "Buffer: 3/100 events" in output


def test_history_stats_table_reports_stored_event_counts():
    output = OutputFormatter._format_history_stats(
        {
            "statistics": {},
            "capacity_info": _capacity_info_with(3),
            "agent_filter": None,
            "timestamp": "2026-01-01T00:00:00",
        }
    )

    assert "Default buffer: 3/100 events" in output
    assert "Retained in all buffers: 3 events" in output


def test_history_stats_table_counts_events_kept_in_a_policy_store():
    """Heartbeats live in their own store; the breakdown must still show them."""
    store = EventStore(
        capacity=100, event_policies={"agent_heartbeat": BucketRingStore(2)}
    )
    for index in range(4):
        store.record(category="orchestrator", event_name="agent_started")
    for index in range(6):
        store.record(
            category="agent", event_name="agent_heartbeat", agent=f"worker-{index % 2}"
        )

    output = OutputFormatter._format_history_stats(
        {
            "statistics": store.stats(),
            "capacity_info": store.get_capacity_info(),
            "agent_filter": None,
            "timestamp": "2026-01-01T00:00:00",
        }
    )

    # The default buffer holds only the 4 non-heartbeat events...
    assert "Default buffer: 4/100 events" in output
    # ...while the breakdown accounts for every event recorded, heartbeats
    # included, even though the bucket store evicted two of them.
    assert "agent_started" in output and "agent_heartbeat" in output
    assert "recorded since start" in output
    breakdown = dict(
        (line.split()[0], int(line.split()[1]))
        for line in output.splitlines()
        if line.startswith("  ")
    )
    assert breakdown == {"agent_started": 4, "agent_heartbeat": 6}


def test_stop_reports_the_message_of_the_orchestrator(cli_response):
    output = OutputFormatter.format_response("stop", cli_response("stop", ["worker"]))

    assert output == "Stop requested for agent worker"


def test_start_reports_how_the_worker_pool_handled_the_request(cli_response):
    output = OutputFormatter.format_response("start", cli_response("start", ["worker"]))

    assert output.startswith("Agent worker start initiated (")
    assert "started" in output


def test_shutdown_is_reported_as_a_message_not_as_raw_json(cli_response):
    output = OutputFormatter.format_response("shutdown", cli_response("shutdown"))

    assert output == "Orchestrator shutdown initiated"


def test_ps_counts_the_registered_agents_not_the_worker_slots(cli_response):
    output = OutputFormatter.format_response("ps", cli_response("ps"))

    assert output.startswith("Orchestrator Status: 0/2 agents running (5 worker slots)")


def test_stats_does_not_clear_redirected_output(stats_command, capfd):
    stats_command._display_stats_iteration()

    output = capfd.readouterr().out

    assert "\x1b[" not in output  # no clear-screen escapes in a pipe
    assert "AGENT STATS" in output
    assert "worker" in output


def test_orchestrator_status_formats_zmq_address():
    output = OutputFormatter._format_status(
        {
            "total_agents": 0,
            "running_agents": 0,
            "max_workers": 5,
            "waiting_agents": 0,
            "command_interface_enabled": True,
            "command_zmq_address": "tcp://*:5555",
        }
    )

    assert "ZeroMQ Address: tcp://*:5555" in output
    assert "Socket Path" not in output
