import pytest
from fastapi import HTTPException

from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator, RunMode
from PyOrchestrate.web_interface import server
from PyOrchestrate.web_interface.server import (
    OrchestratorClient,
    WebServerConfig,
    create_app,
)

ZMQ_ADDRESS = "tcp://127.0.0.1:5666"


@pytest.fixture
def orchestrator():
    result = Orchestrator(
        config=Orchestrator.Config(
            run_mode=RunMode.DAEMON,
            enable_command_interface=True,
            command_zmq_address=ZMQ_ADDRESS,
        ),
        name="web_orchestrator",
    )

    yield result

    result.shutdown()


class SilentChannel:
    """A channel that accepts the request and never answers it.

    Standing in for an orchestrator that is not listening: the real one keeps
    the caller waiting for the full `send_and_receive` timeout, which is the
    only reason this is not driven over a socket.
    """

    def __init__(self, a_type, zmq_address):
        self.zmq_address = zmq_address

    def send_and_receive(self, msg, timeout=5.0):
        return None


class BrokenChannel:
    """A channel that cannot be opened at all, as for a malformed address."""

    def __init__(self, a_type, zmq_address):
        raise ValueError(f"Invalid argument: {zmq_address}")


def test_web_server_defaults_to_cli_zmq_address():
    config = WebServerConfig()

    assert config.port == 8000
    assert config.socket_path == "tcp://127.0.0.1:5555"


def test_web_server_only_exposes_supported_orchestrator_routes():
    app = create_app(WebServerConfig())
    routes = {route.path for route in app.routes}

    assert "/api/orchestrator/status" in routes
    assert "/api/orchestrator/stats" in routes
    assert "/api/orchestrator/report" not in routes


def test_the_client_returns_the_payload_of_a_running_orchestrator(orchestrator):
    payload = OrchestratorClient(ZMQ_ADDRESS).send_command("status")

    assert payload["status"] == "success"
    assert payload["data"]["command_zmq_address"] == ZMQ_ADDRESS


def test_an_unreachable_orchestrator_is_reported_as_unavailable(monkeypatch):
    """The 503 was raised inside the try that answers 500, and lost to it."""
    monkeypatch.setattr(server, "MessageChannel", SilentChannel)

    with pytest.raises(HTTPException) as error:
        OrchestratorClient("tcp://127.0.0.1:5999").send_command("ps")

    assert error.value.status_code == 503
    assert error.value.detail == (
        "Cannot connect to orchestrator at tcp://127.0.0.1:5999"
    )


def test_a_transport_failure_is_still_reported_as_a_server_error(monkeypatch):
    monkeypatch.setattr(server, "MessageChannel", BrokenChannel)

    with pytest.raises(HTTPException) as error:
        OrchestratorClient("not-a-zmq-address").send_command("ps")

    assert error.value.status_code == 500
    assert error.value.detail.startswith("Communication error:")


def test_a_command_error_is_returned_as_a_payload_not_as_a_status_code(orchestrator):
    """The interface is a passthrough: failures keep their structured payload."""
    payload = OrchestratorClient(ZMQ_ADDRESS).send_command("status", ["ghost"])

    assert payload["status"] == "error"
    assert payload["code"] == 404
    assert payload["error"] == "Agent ghost not found"
