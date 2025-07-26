import os
import socket
import threading
from typing import Optional


class CommandServer:
    """Simple UNIX socket server to accept orchestrator commands."""

    def __init__(self, orchestrator: "Orchestrator", socket_path: str):
        self.orchestrator = orchestrator
        self.socket_path = socket_path
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None
        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except OSError:
                pass

    def _run(self) -> None:
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(self.socket_path)
        server.listen(1)
        while self._running:
            try:
                server.settimeout(1.0)
                conn, _ = server.accept()
            except socket.timeout:
                continue
            with conn:
                try:
                    data = conn.recv(1024).decode().strip()
                except Exception:
                    continue
                if not data:
                    continue
                response = self.orchestrator.process_command(data)
                try:
                    conn.sendall(response.encode() + b"\n")
                except Exception:
                    pass
        server.close()
