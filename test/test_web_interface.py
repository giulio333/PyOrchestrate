from PyOrchestrate.web_interface.server import WebServerConfig, create_app


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
