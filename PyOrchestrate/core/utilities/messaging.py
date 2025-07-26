import queue
import multiprocessing
import socket
import os
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Union, Optional, Literal


@dataclass
class ServiceMessage:
    sender: str
    type: Literal["COMMAND", "STATUS"]
    payload: str
    timestamp: datetime


class MessageChannel:
    """
    A class that provides a message channel for communication between agents and orchestrators.

    A MessageChannel is a communication channel that can be used to send and receive messages
    between different components of the system. It can be used for both threading and multiprocessing
    scenarios. The channel can be configured to use either a thread-safe queue or a process-safe queue
    depending on the type of communication required.
    """

    def __init__(self, a_type: str, socket_path: str = "/tmp/pyorchestrate.sock"):
        self.a_type = a_type
        self.socket_path = socket_path

        if a_type == "thread":
            self._queue = queue.Queue()
        elif a_type == "process":
            self._queue = multiprocessing.Queue()
        elif a_type == "unix_socket":
            self._setup_unix_socket()
        else:
            raise ValueError(
                "Invalid a_type. Must be 'thread', 'process', or 'unix_socket'."
            )

    def _setup_unix_socket(self):
        """Setup UNIX domain socket for external communication."""
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Remove socket file if it exists
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

        # Bind and listen
        self._socket.bind(self.socket_path)
        self._socket.listen(5)
        self._socket.settimeout(1.0)  # Non-blocking with timeout

        self._clients = []  # Store client connections

    def send(self, target: str, msg: ServiceMessage) -> None:
        if self.a_type in ["thread", "process"]:
            self._queue.put((target, msg))
        elif self.a_type == "unix_socket":
            # Send to all connected clients
            msg_data = (
                json.dumps(
                    {
                        "sender": msg.sender,
                        "type": msg.type,
                        "payload": msg.payload,
                        "timestamp": msg.timestamp.isoformat(),
                    }
                ).encode()
                + b"\n"
            )

            for client in self._clients[
                :
            ]:  # Use slice copy to avoid modification during iteration
                try:
                    client.send(msg_data)
                except:
                    # Remove disconnected clients
                    self._clients.remove(client)
                    client.close()

    def receive(self, timeout: Optional[float] = None) -> Optional[ServiceMessage]:
        if self.a_type in ["thread", "process"]:
            try:
                target, msg = self._queue.get(timeout=timeout)
                return msg
            except queue.Empty:
                return None
        elif self.a_type == "unix_socket":
            try:
                # Accept new connections
                try:
                    client_socket, _ = self._socket.accept()
                    self._clients.append(client_socket)
                except socket.timeout:
                    pass  # No new connections

                # Check for messages from existing clients
                for client in self._clients[:]:
                    try:
                        client.settimeout(0.1)  # Short timeout for non-blocking read
                        data = client.recv(4096)
                        if data:
                            msg_str = data.decode().strip()
                            msg_data = json.loads(msg_str)
                            return ServiceMessage(
                                sender=msg_data["sender"],
                                type=msg_data["type"],
                                payload=msg_data["payload"],
                                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                            )
                    except (socket.timeout, json.JSONDecodeError, KeyError):
                        pass  # No data or invalid data
                    except:
                        # Remove disconnected clients
                        self._clients.remove(client)
                        client.close()

                return None
            except Exception:
                return None

    def close(self):
        """Close the message channel and cleanup resources."""
        if self.a_type == "unix_socket":
            # Close all client connections
            for client in self._clients:
                client.close()
            self._clients.clear()

            # Close server socket
            self._socket.close()

            # Remove socket file
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
