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
    print(f"Orchestrator Status:")
    print(f"  Total agents: {status.get('total_agents', 'unknown')}")
    print(f"  Running agents: {status.get('running_agents', 'unknown')}")
    print(f"  Waiting agents: {status.get('waiting_agents', 'unknown')}")
    print(f"  Max workers: {status.get('max_workers', 'unknown')}")
    print(f"  Socket path: {status.get('command_socket_path', 'unknown')}")
else:
    print("Failed to get orchestrator status")
