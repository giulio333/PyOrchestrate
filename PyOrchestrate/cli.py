import argparse
import os
import socket
import json
import time
import signal
import sys
from datetime import datetime

from PyOrchestrate.core.utilities.messaging import (
    MessageChannel,
    ServiceMessage,
)


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
    """Send a command to a running orchestrator via MessageChannelClient."""
    try:
        # Create MessageChannel client
        client = MessageChannel("unix_socket_client", args.socket)

        # Prepare command using new standardized request format
        command = args.command[0] if args.command else "status"
        cmd_args = args.command[1:] if len(args.command) > 1 else []

        msg = ServiceMessage.create_command(
            sender="cli",
            command=command,
            args=cmd_args,
        )

        # Send command and receive response
        response_msg = client.send_and_receive(msg, timeout=5.0)

        if response_msg:
            response_payload = response_msg.payload  # Now already a dict

            # Format output
            if response_payload.get("status") == "success":
                if hasattr(args, "format") and args.format == "json":
                    # Print only the data section for machine-friendly output
                    print(
                        json.dumps(
                            response_payload.get("data", {}),
                            indent=2,
                            ensure_ascii=False,
                        )
                    )
                else:
                    print_formatted_response(command, response_payload)
            else:
                # Error responses: JSON if requested, otherwise human message
                if hasattr(args, "format") and args.format == "json":
                    print(json.dumps(response_payload, indent=2, ensure_ascii=False))
                else:
                    print(f"Error: {response_payload.get('message', 'Unknown error')}")
        else:
            print(
                f"Error: Cannot connect to socket {args.socket}. Is the orchestrator running with command interface enabled?"
            )

    except ImportError:
        print(
            "Error: Cannot import MessageChannelClient. PyOrchestrate not properly installed."
        )
    except Exception as e:
        print(f"Error: {e}")


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

    elif command == "history":
        events = data.get("events", [])
        count = data.get("count", 0)
        filters = data.get("filters", {})
        capacity_info = data.get("capacity_info", {})

        print(f"=== Event History ({count} events) ===")
        if filters:
            filter_parts = []
            if filters.get("agent"):
                filter_parts.append(f"agent={filters['agent']}")
            if filters.get("type"):
                filter_parts.append(f"type={filters['type']}")
            if filters.get("last"):
                filter_parts.append(f"last={filters['last']}")
            if filters.get("after_seq"):
                filter_parts.append(f"after_seq={filters['after_seq']}")

            if filter_parts:
                print(f"Filters: {', '.join(filter_parts)}")

        print(
            f"Buffer: {capacity_info.get('current_size', 0)}/{capacity_info.get('capacity', 0)} events"
        )
        print()

        if events:
            print(
                f"{'SEQ':<6} {'TIME':<19} {'CATEGORY':<12} {'TYPE':<20} {'AGENT':<15} {'SEV':<5}"
            )
            print("-" * 80)
            for event in events:
                timestamp = event.get("timestamp", "")[:19]  # Truncate timestamp
                category = event.get("category", "")[:11]
                event_type = event.get("type", "")[:19]
                agent = (event.get("agent") or "")[:14]
                severity = event.get("severity", "")[:4]
                seq = event.get("seq", 0)

                print(
                    f"{seq:<6} {timestamp:<19} {category:<12} {event_type:<20} {agent:<15} {severity:<5}"
                )
        else:
            print("No events found")

    elif command == "history-stats":
        statistics = data.get("statistics", {})
        capacity_info = data.get("capacity_info", {})
        agent_filter = data.get("agent_filter")
        timestamp = data.get("timestamp", "")

        print("=== Event Statistics ===")
        print(f"Timestamp: {timestamp}")
        if agent_filter:
            print(f"Agent Filter: {agent_filter}")
        print(
            f"Buffer: {capacity_info.get('current_size', 0)}/{capacity_info.get('capacity', 0)} events"
        )
        print(f"Total Events: {capacity_info.get('total_events', 0)}")
        print()

        by_type = statistics.get("by_type", {})
        if by_type:
            print("Event Type Breakdown:")
            # Sort by count descending
            sorted_events = sorted(by_type.items(), key=lambda x: x[1], reverse=True)
            for event_type, count in sorted_events:
                print(f"  {event_type:<25} {count:>6}")
        else:
            print("No event statistics available")

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
        ("history", "Get event history with optional filtering"),
        ("history-stats", "Get aggregated event statistics"),
    ]:
        cmd_parser = subparsers.add_parser(cmd_name, help=cmd_help)
        cmd_parser.add_argument(
            "--socket",
            default="/tmp/pyorchestrate.sock",
            help="Path to orchestrator socket (default: /tmp/pyorchestrate.sock)",
        )
        if cmd_name in ["status", "stop", "start"]:
            cmd_parser.add_argument("agent_name", nargs="?", help="Agent name")
        elif cmd_name in ["history", "history-stats"]:
            cmd_parser.add_argument("--last", type=int, help="Number of last events")
            cmd_parser.add_argument("--agent", type=str, help="Filter by agent name")
            cmd_parser.add_argument("--type", type=str, help="Filter by event type")
            cmd_parser.add_argument(
                "--after-seq", type=int, help="Filter by sequence number"
            )
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
    elif command in ["history", "history-stats"]:
        # For history commands, create a parameters dict
        params = {}
        if hasattr(args, "last") and args.last is not None:
            params["last"] = args.last
        if hasattr(args, "agent") and args.agent is not None:
            params["agent"] = args.agent
        if hasattr(args, "type") and args.type is not None:
            params["type"] = args.type
        if hasattr(args, "after_seq") and args.after_seq is not None:
            params["after_seq"] = args.after_seq

        # Pass parameters as JSON string
        args.command = [command, json.dumps(params)]
    elif hasattr(args, "filters") and args.filters:
        args.command = [command, args.filters]
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
                # Create MessageChannel client
                client = MessageChannel("unix_socket_client", args.socket)

                msg = ServiceMessage.create_command(
                    sender="cli",
                    command="stats",
                    args=[],
                )

                # Send command and receive response
                response_msg = client.send_and_receive(
                    msg, timeout=5.0, auto_close=True
                )

                if response_msg:
                    response_payload = response_msg.payload  # Already a dict

                    if response_payload.get("status") == "success":
                        print_stats_output(response_payload)
                    else:
                        print(
                            f"Error: {response_payload.get('message', 'Unknown error')}"
                        )
                else:
                    print(f"Error: Cannot connect to socket {args.socket}")
                    print("Is the orchestrator running with command interface enabled?")
                    break

            except Exception as e:
                print(f"Error: {e}")
                break

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
