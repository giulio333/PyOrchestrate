import json
import subprocess
from typing import Any, cast, Literal

from PyOrchestrate.core.utilities.messaging import (
    MessageChannel,
    ServiceMessage,
)


def get_orchestrator_status_via_cli() -> Any:
    try:
        result = subprocess.run(
            ["pyorchestrate", "history", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return None


def get_orchestrator_status_via_channel(socket_name: str) -> Any:
    client = MessageChannel(cast(Literal["unix_socket_client"], socket_name))
    msg = ServiceMessage.create_command(
        "test", "history", [{"agent": "FileWriter"}], "giulio333"
    )
    response: ServiceMessage | None = client.send_and_receive(msg, timeout=5)
    if response:
        return response.to_json(indent=2)
    return None


if __name__ == "__main__":
    # Example 1: use CLI (requires `pyorchestrate` command to be available in PATH)
    cli_status = get_orchestrator_status_via_cli()
    if cli_status:
        print("Orchestrator status via CLI:")
        print(json.dumps(cli_status, indent=2))
    else:
        print("Impossibile ottenere lo status via CLI")

    # Example 2: use MessageChannel
    channel_status = get_orchestrator_status_via_channel("unix_socket_client")
    if channel_status:
        print("Orchestrator status via MessageChannel:")
        print(channel_status)
    else:
        print("Impossibile ottenere lo status via MessageChannel")
