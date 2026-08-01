import json
from unittest.mock import MagicMock

from PyOrchestrate.cli import (
    ArgumentParser,
    CLIConstants,
    OrchestratorCommand,
    OutputFormatter,
)
from PyOrchestrate.core.orchestrator.event_store import EventStore


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

    assert "Buffer: 3/100 events" in output
    assert "Total Events: 3" in output


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
