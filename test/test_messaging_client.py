"""Tests for MessageChannel client functionality."""

import pytest
import tempfile
import os
import json
import threading
import time
from datetime import datetime
from PyOrchestrate.core.utilities.messaging import MessageChannel, ServiceMessage


class TestMessageChannelClient:
    """Test MessageChannel client communication with MessageChannel server."""

    def test_basic_communication(self):
        """Test basic send and receive functionality."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            socket_path = os.path.join(tmp_dir, "test.sock")

            # Start server in background thread
            server = MessageChannel("unix_socket", socket_path)

            def server_loop():
                # Wait for client message
                msg = server.receive(timeout=2.0)
                if msg:
                    # Echo back a response
                    response = ServiceMessage(
                        sender="server",
                        type="STATUS",
                        payload=json.dumps(
                            {"status": "success", "data": {"echo": "response"}}
                        ),
                        timestamp=datetime.now(),
                    )
                    server.send("client", response)

            server_thread = threading.Thread(target=server_loop)
            server_thread.start()

            # Give server time to start
            time.sleep(0.1)

            # Create client and send message
            client = MessageChannel("unix_socket_client", socket_path)
            request = ServiceMessage(
                sender="client",
                type="COMMAND",
                payload=json.dumps({"command": "test"}),
                timestamp=datetime.now(),
            )

            response = client.send_and_receive(request, timeout=2.0)

            # Verify response
            assert response is not None
            assert response.sender == "server"
            assert response.type == "STATUS"

            response_data = json.loads(response.payload)
            assert response_data["status"] == "success"
            assert response_data["data"]["echo"] == "response"

            # Cleanup
            server_thread.join(timeout=1.0)
            server.close()

    def test_connection_failure(self):
        """Test behavior when server is not available."""
        client = MessageChannel("unix_socket_client", "/nonexistent/socket")
        request = ServiceMessage(
            sender="client",
            type="COMMAND",
            payload=json.dumps({"command": "test"}),
            timestamp=datetime.now(),
        )

        response = client.send_and_receive(request, timeout=1.0)
        assert response is None

    def test_timeout_handling(self):
        """Test timeout behavior when server doesn't respond."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            socket_path = os.path.join(tmp_dir, "test.sock")

            # Start server that doesn't respond
            server = MessageChannel("unix_socket", socket_path)

            def server_loop():
                # Receive but don't respond
                server.receive(timeout=2.0)

            server_thread = threading.Thread(target=server_loop)
            server_thread.start()

            time.sleep(0.1)

            # Client should timeout
            client = MessageChannel("unix_socket_client", socket_path)
            request = ServiceMessage(
                sender="client",
                type="COMMAND",
                payload=json.dumps({"command": "test"}),
                timestamp=datetime.now(),
            )

            start_time = time.time()
            response = client.send_and_receive(request, timeout=0.5)
            elapsed = time.time() - start_time

            assert response is None
            assert elapsed >= 0.5  # Should respect timeout
            assert elapsed < 1.0  # Should not take much longer

            # Cleanup
            server_thread.join(timeout=1.0)
            server.close()

    def test_message_format_compatibility(self):
        """Test that MessageChannelClient produces same format as original CLI."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            socket_path = os.path.join(tmp_dir, "test.sock")

            server = MessageChannel("unix_socket", socket_path)
            received_message = None

            def server_loop():
                nonlocal received_message
                received_message = server.receive(timeout=2.0)

            server_thread = threading.Thread(target=server_loop)
            server_thread.start()

            time.sleep(0.1)

            # Send message with client
            client = MessageChannel("unix_socket_client", socket_path)
            request = ServiceMessage(
                sender="cli",
                type="COMMAND",
                payload=json.dumps({"command": "status", "args": []}),
                timestamp=datetime.now(),
            )

            client._connect_to_server()
            client._send_to_unix_socket_client(request)
            client.close()

            server_thread.join(timeout=1.0)

            # Verify message format
            assert received_message is not None
            assert received_message.sender == "cli"
            assert received_message.type == "COMMAND"

            payload_data = json.loads(received_message.payload)
            assert payload_data["command"] == "status"
            assert payload_data["args"] == []

            server.close()


if __name__ == "__main__":
    pytest.main([__file__])
