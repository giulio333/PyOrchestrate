import json
from unittest.mock import MagicMock

from PyOrchestrate.cli import (
    ArgumentParser,
    CLIConstants,
    OrchestratorCommand,
    OutputFormatter,
)


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


def test_history_table_formats_event_name_filter():
    output = OutputFormatter._format_history(
        {
            "events": [],
            "count": 0,
            "filters": {"event_name": "AGENT_STARTED"},
            "capacity_info": {"current_size": 0, "capacity": 100},
        }
    )

    assert "Filters: type=AGENT_STARTED" in output


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
