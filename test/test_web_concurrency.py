"""Exercise the HTTP application and real ZeroMQ waits without an HTTP client extra."""

import asyncio
import json
import threading

import pytest
import zmq

from PyOrchestrate.web_interface import server
from PyOrchestrate.web_interface.server import WebServerConfig, create_app


async def request(app, path):
    messages = []
    path, _, query = path.partition("?")
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": query.encode(),
        "headers": [(b"accept", b"application/json")],
        "client": ("127.0.0.1", 12345),
        "server": ("test", 80),
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)
    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in messages)
    return status, json.loads(body)


@pytest.fixture
def silent_peer():
    ready = threading.Event()
    received_all = threading.Event()
    stop = threading.Event()
    addresses = []
    commands = []

    def serve():
        with zmq.Context() as context, context.socket(zmq.ROUTER) as socket:
            socket.linger = 0
            port = socket.bind_to_random_port("tcp://127.0.0.1")
            addresses.append(f"tcp://127.0.0.1:{port}")
            ready.set()
            while not stop.is_set():
                if socket.poll(50):
                    commands.append(json.loads(socket.recv_multipart()[-1])["payload"])
                    if len(commands) == 7:
                        received_all.set()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    assert ready.wait(5), "ZeroMQ peer failed to bind"
    try:
        yield addresses[0], received_all, commands
    finally:
        stop.set()
        thread.join(timeout=2)
        assert not thread.is_alive()


@pytest.fixture
def tracked_channels(monkeypatch):
    channels = []
    closed = []

    class TrackedChannel(server.MessageChannel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            channels.append((self, threading.get_ident()))

        def close(self):
            closed.append((self, threading.get_ident()))
            super().close()

    monkeypatch.setattr(server, "MessageChannel", TrackedChannel)
    try:
        yield channels, closed
    finally:
        for channel, _ in channels:
            channel.close()


def test_all_monitoring_routes_can_wait_without_blocking_health(
    silent_peer, tracked_channels
):
    address, received_all, commands = silent_peer
    app = create_app(WebServerConfig(socket_path=address))
    paths = [
        "/api/orchestrator/status",
        "/api/agents",
        "/api/agents/ghost",
        "/api/orchestrator/dependencies",
        "/api/orchestrator/stats",
        "/api/history?agent=Worker&last=2&after_seq=1&event_type=AGENT_ERROR",
        "/api/history/stats?agent=Worker",
    ]

    async def exercise():
        pending = [asyncio.create_task(request(app, path)) for path in paths]
        try:
            received = await asyncio.to_thread(received_all.wait, 2)
            health_status, health = await request(app, "/api/health")
            assert received, "Monitoring requests could not reach ZeroMQ concurrently"
            assert health_status == 200
            assert health["status"] == "healthy"
            assert all(not task.done() for task in pending)
        finally:
            responses = await asyncio.gather(*pending)
        assert all(status == 503 for status, _ in responses)
        assert all(
            body["detail"] == f"Cannot connect to orchestrator at {address}"
            for _, body in responses
        )

    asyncio.run(exercise())
    channels, closed = tracked_channels
    assert len(channels) == 7
    assert len(closed) == 7
    assert set(closed) == set(channels)
    assert all(owner != threading.get_ident() for _, owner in channels)
    by_command = {item["command"]: item["args"] for item in commands}
    assert len(commands) == 7
    assert set(by_command) == {
        "status",
        "ps",
        "dependencies",
        "stats",
        "history",
        "history-stats",
    }
    assert any(
        item["command"] == "status" and item["args"] == ["ghost"] for item in commands
    )
    assert json.loads(by_command["history"][0]) == {
        "agent": "Worker",
        "last": 2,
        "after_seq": 1,
        "event_name": "AGENT_ERROR",
    }
    assert json.loads(by_command["history-stats"][0]) == {"agent": "Worker"}
