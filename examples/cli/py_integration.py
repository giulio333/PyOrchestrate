import json
import subprocess


def get_orchestrator_status(socket_path):
    """Get orchestrator status via CLI."""
    try:
        result = subprocess.run(
            ["pyorchestrate", "status", "--socket", socket_path, "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return None


# Usage
status = get_orchestrator_status("/tmp/pyorchestrate.sock")
if status:
    if status.get("status") == "success":
        data = status["data"]
        print(f"Orchestrator Status:")
        print(f"  Total agents: {data.get('total_agents', 'unknown')}")
        print(f"  Running agents: {data.get('running_agents', 'unknown')}")
        print(f"  Waiting agents: {data.get('waiting_agents', 'unknown')}")
        print(f"  Max workers: {data.get('max_workers', 'unknown')}")
        print(f"  Socket path: {data.get('command_socket_path', 'unknown')}")
    else:
        print(f"Error: {status.get('message', 'Unknown error')}")
else:
    print("Failed to get orchestrator status")
