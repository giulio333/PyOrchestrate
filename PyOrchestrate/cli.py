import argparse
import os
import socket
import json
import time
import signal
import sys
from datetime import datetime


def create_project_structure(app_name):
    """
    Create the project structure for the specified app name.
    """
    os.makedirs(f"{app_name}/models", exist_ok=True)
    os.makedirs(f"{app_name}/configurations", exist_ok=True)
    with open(f"{app_name}/starter.py", "w") as f:
        f.write(starter_template)


starter_template = """import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Imports
from PyOrchestrate.core.orchestrator import Orchestrator

if __name__ == "__main__":

    # Initialize Orchestrator with command interface enabled
    config = Orchestrator.Config(
        enable_command_interface=True,
        command_socket_path="/tmp/pyorchestrate.sock"
    )
    orchestrator = Orchestrator(config=config)

    # Register Agents
    # orchestrator.register_agent(YouAgent, "YourAgentName")

    # Start Orchestrator
    orchestrator.start()

    # Join Agents
    orchestrator.join()
"""


def start_command(args: argparse.Namespace) -> None:
    """Handle the ``create`` subcommand."""
    create_project_structure(args.app_name)
    print(f"Project structure for '{args.app_name}' created successfully.")
    print(
        f"📁 Created directories: {args.app_name}/models, {args.app_name}/configurations"
    )
    print(f"📄 Created file: {args.app_name}/starter.py")
    print(f"\n🚀 To get started:")
    print(f"   cd {args.app_name}")
    print(f"   python starter.py")
    print(f"\n📋 Then use CLI commands to control it:")
    print(f"   python -m PyOrchestrate.cli ps")
    print(f"   python -m PyOrchestrate.cli shutdown")


def send_command(args: argparse.Namespace) -> None:
    """Send a command to a running orchestrator via UNIX socket."""
    try:
        # Create socket connection
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(args.socket)

        # Prepare command message
        cmd_data = {
            "command": args.command[0] if args.command else "status",
            "args": args.command[1:] if len(args.command) > 1 else [],
        }

        msg_data = {
            "sender": "cli",
            "type": "COMMAND",
            "payload": json.dumps(cmd_data),
            "timestamp": datetime.now().isoformat(),
        }

        # Send command
        sock.send(json.dumps(msg_data).encode() + b"\n")

        # Receive response
        sock.settimeout(5.0)  # 5 second timeout
        response_data = sock.recv(4096).decode().strip()

        if response_data:
            response_msg = json.loads(response_data)
            response_payload = json.loads(response_msg["payload"])

            # Format output
            if response_payload.get("status") == "success":
                if args.format == "json":
                    print(json.dumps(response_payload, indent=2))
                else:
                    print_formatted_response(
                        args.command[0] if args.command else "status", response_payload
                    )
            else:
                print(f"Error: {response_payload.get('message', 'Unknown error')}")
        else:
            print("No response received from orchestrator")

    except FileNotFoundError:
        print(
            f"Error: Cannot connect to socket {args.socket}. Is the orchestrator running with command interface enabled?"
        )
    except json.JSONDecodeError as e:
        print(f"Error: Invalid response format: {e}")
    except socket.timeout:
        print("Error: Timeout waiting for response from orchestrator")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            sock.close()
        except:
            pass


def print_formatted_response(command: str, response_data: dict) -> None:
    """Print formatted response based on command type."""
    data = response_data.get("data", {})

    if command in ["ps", "list"]:
        agents = data.get("agents", [])
        print(
            f"Orchestrator Status: {data.get('running_count', 0)}/{data.get('max_workers', 0)} agents running"
        )
        if data.get("waiting_count", 0) > 0:
            print(f"Waiting in queue: {data.get('waiting_count', 0)}")
        print()

        if agents:
            print(f"{'Name':<20} {'Status':<10} {'Started':<8} {'In Queue':<8}")
            print("-" * 50)
            for agent in agents:
                status = "ALIVE" if agent.get("alive") else "DEAD"
                started = "YES" if agent.get("started") else "NO"
                queued = "YES" if agent.get("in_queue") else "NO"
                print(f"{agent['name']:<20} {status:<10} {started:<8} {queued:<8}")
        else:
            print("No agents registered")

    elif command == "status":
        if "name" in data:  # Agent status
            print(f"Agent: {data['name']}")
            print(f"Alive: {data.get('alive', False)}")
            print(f"Started: {data.get('started', False)}")
            print(f"In Queue: {data.get('in_queue', False)}")
            if data.get("dependencies"):
                print(f"Dependencies: {', '.join(data['dependencies'])}")
        else:  # Orchestrator status
            print(f"Total Agents: {data.get('total_agents', 0)}")
            print(f"Running Agents: {data.get('running_agents', 0)}")
            print(f"Max Workers: {data.get('max_workers', 0)}")
            print(f"Waiting Agents: {data.get('waiting_agents', 0)}")
            print(
                f"Command Interface: {'Enabled' if data.get('command_interface_enabled') else 'Disabled'}"
            )
            if data.get("command_socket_path"):
                print(f"Socket Path: {data['command_socket_path']}")

    elif command == "dependencies":
        deps = data.get("dependencies", {})
        if deps:
            print("Agent Dependencies:")
            for agent, deps_list in deps.items():
                if deps_list:
                    print(f"  {agent} -> {', '.join(deps_list)}")
        else:
            print("No dependencies configured")

    elif command in ["start", "stop"]:
        print(response_data.get("message", "Operation completed"))

    elif command == "report":
        orchestrator_data = data.get("orchestrator", {})
        agents = data.get("agents", [])
        dependencies = data.get("dependencies", {})

        print("=== Orchestrator Report ===")
        print(f"Running Agents: {orchestrator_data.get('running_agents', 0)}")
        print(f"Max Workers: {orchestrator_data.get('max_workers', 0)}")
        print(f"Waiting Agents: {orchestrator_data.get('waiting_agents', 0)}")
        print(f"Check Interval: {orchestrator_data.get('check_interval', 0)}s")
        print()

        if agents:
            print("=== Agents ===")
            for agent in agents:
                print(f"  {agent['name']}: {'ALIVE' if agent.get('alive') else 'DEAD'}")

        if dependencies:
            print("\n=== Dependencies ===")
            for agent, deps in dependencies.items():
                if deps:
                    print(f"  {agent} -> {', '.join(deps)}")

    else:
        print(json.dumps(response_data, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="PyOrchestrate CLI")
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="PyOrchestrate version 0.2.0",
    )

    subparsers = parser.add_subparsers(dest="command")

    # Project creation command
    create_parser = subparsers.add_parser(
        "create", help="Create a new project structure with the specified app name"
    )
    create_parser.add_argument("app_name", help="Name of the app to create")
    create_parser.set_defaults(func=start_command)

    # External command interface
    for cmd_name, cmd_help in [
        ("ps", "List all agents and their status"),
        ("list", "List all agents and their status"),
        ("status", "Get orchestrator or agent status"),
        ("report", "Get full orchestrator report"),
        ("dependencies", "Show agent dependencies"),
        ("start", "Start a specific agent"),
        ("stop", "Stop a specific agent"),
        ("shutdown", "Shutdown the orchestrator gracefully"),
    ]:
        cmd_parser = subparsers.add_parser(cmd_name, help=cmd_help)
        cmd_parser.add_argument(
            "--socket",
            default="/tmp/pyorchestrate.sock",
            help="Path to orchestrator socket (default: /tmp/pyorchestrate.sock)",
        )
        if cmd_name in ["status", "stop", "start"]:
            cmd_parser.add_argument("agent_name", nargs="?", help="Agent name")
        cmd_parser.add_argument(
            "--format", choices=["table", "json"], default="table", help="Output format"
        )
        cmd_parser.set_defaults(
            func=lambda args, cmd=cmd_name: send_command_wrapper(args, cmd)
        )

    # Special stats command with real-time monitoring
    stats_parser = subparsers.add_parser(
        "stats", help="Display real-time stats of all agents (like docker stats)"
    )
    stats_parser.add_argument(
        "--socket",
        default="/tmp/pyorchestrate.sock",
        help="Path to orchestrator socket (default: /tmp/pyorchestrate.sock)",
    )
    stats_parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Refresh interval in seconds (default: 2.0)",
    )
    stats_parser.set_defaults(func=stats_command)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


def send_command_wrapper(args: argparse.Namespace, command: str) -> None:
    """Wrapper to handle different command types."""
    if hasattr(args, "agent_name") and args.agent_name:
        args.command = [command, args.agent_name]
    else:
        args.command = [command]

    send_command(args)


def stats_command(args: argparse.Namespace) -> None:
    """Display real-time stats of all agents like docker stats."""

    def signal_handler(sig, frame):
        """Handle Ctrl+C gracefully."""
        print("\n\nMonitoring stopped.")
        sys.exit(0)

    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)

    print("AGENT STATS - Press Ctrl+C to stop")
    print("=" * 80)

    try:
        while True:
            # Clear screen (works on most terminals)
            os.system("clear" if os.name == "posix" else "cls")

            print("AGENT STATS - Press Ctrl+C to stop")
            print("=" * 80)

            # Get stats from orchestrator
            try:
                # Create socket connection
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(args.socket)

                # Prepare stats command
                cmd_data = {
                    "command": "stats",
                    "args": [],
                }

                msg_data = {
                    "sender": "cli",
                    "type": "COMMAND",
                    "payload": json.dumps(cmd_data),
                    "timestamp": datetime.now().isoformat(),
                }

                # Send command
                sock.send(json.dumps(msg_data).encode() + b"\n")

                # Receive response
                sock.settimeout(5.0)
                response_data = sock.recv(8192).decode().strip()

                if response_data:
                    response_msg = json.loads(response_data)
                    response_payload = json.loads(response_msg["payload"])

                    if response_payload.get("status") == "success":
                        print_stats_output(response_payload)
                    else:
                        print(
                            f"Error: {response_payload.get('message', 'Unknown error')}"
                        )
                else:
                    print("No response received from orchestrator")

            except FileNotFoundError:
                print(f"Error: Cannot connect to socket {args.socket}")
                print("Is the orchestrator running with command interface enabled?")
                break
            except Exception as e:
                print(f"Error: {e}")
                break
            finally:
                try:
                    sock.close()
                except:
                    pass

            # Wait before next update
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")


def print_stats_output(response_data: dict) -> None:
    """Print formatted stats output."""
    data = response_data.get("data", {})

    # Print orchestrator info
    orch_data = data.get("orchestrator", {})
    timestamp = data.get("timestamp", "")

    print(f"Timestamp: {timestamp}")
    print(
        f"Running: {orch_data.get('running_agents', 0)}/{orch_data.get('max_workers', 0)} agents"
    )
    print(f"Waiting: {orch_data.get('waiting_agents', 0)} agents")
    print()

    # Print agent stats table
    agents = data.get("agents", [])
    if agents:
        # Header
        print(
            f"{'NAME':<20} {'STATUS':<8} {'PID':<8} {'CPU %':<8} {'MEM MB':<10} {'MEM %':<8} {'THREADS':<8} {'UPTIME':<12}"
        )
        print("-" * 90)

        # Agent rows
        for agent in agents:
            name = agent.get("name", "")[:19]  # Truncate long names
            status = "ALIVE" if agent.get("alive") else "DEAD"
            pid = str(agent.get("pid", "N/A"))[:7]
            cpu = str(agent.get("cpu_percent", "N/A"))[:7]
            mem_mb = str(agent.get("memory_mb", "N/A"))[:9]
            mem_pct = str(agent.get("memory_percent", "N/A"))[:7]
            threads = str(agent.get("threads", "N/A"))[:7]
            uptime = str(agent.get("uptime", "N/A"))[:11]

            print(
                f"{name:<20} {status:<8} {pid:<8} {cpu:<8} {mem_mb:<10} {mem_pct:<8} {threads:<8} {uptime:<12}"
            )
    else:
        print("No agents registered")


if __name__ == "__main__":
    main()
