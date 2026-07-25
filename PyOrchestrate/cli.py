import argparse
import os
import socket
import json
import time
import signal
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from PyOrchestrate import __version__
from PyOrchestrate.core.utilities.messaging import (
    MessageChannel,
    ServiceMessage,
)


class CLIConstants:
    """Constants used throughout the CLI application."""

    #: Alias of :data:`PyOrchestrate.__version__`, which reads the distribution
    #: metadata: the version is declared only in ``pyproject.toml``. Kept as an
    #: attribute so existing readers of ``CLIConstants.VERSION`` keep working.
    VERSION = __version__
    DEFAULT_ZMQ_ADDRESS = "tcp://127.0.0.1:5555"
    DEFAULT_STATS_INTERVAL = 2.0

    STARTER_TEMPLATE = """import os, sys

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


class CommandClient:
    """Handles communication with the orchestrator via MessageChannel."""

    def __init__(self, zmq_address: str = CLIConstants.DEFAULT_ZMQ_ADDRESS):
        self.zmq_address = zmq_address

    def send_command(
        self, command: str, args: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Send a command to the orchestrator and return the response."""
        try:
            client = MessageChannel("zmq_dealer", self.zmq_address)

            msg = ServiceMessage.create_command(
                sender="cli",
                command=command,
                args=args or [],
            )

            response_msg = client.send_and_receive(msg, timeout=10.0)

            if response_msg:
                return response_msg.payload
            return None

        except ImportError:
            raise RuntimeError(
                "Cannot import MessageChannelClient. PyOrchestrate not properly installed."
            )
        except Exception as e:
            raise RuntimeError(f"Communication error: {e}")


class BaseCommand(ABC):
    """Abstract base class for all CLI commands."""

    def __init__(self, client: CommandClient, formatter: "OutputFormatter"):
        self.client = client
        self.formatter = formatter

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> None:
        """Execute the command with the given arguments."""
        pass


class ProjectCommand(BaseCommand):
    """Handles project creation commands."""

    def execute(self, args: argparse.Namespace) -> None:
        """Create a new project structure."""
        self._create_project_structure(args.app_name)

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

    def _create_project_structure(self, app_name: str) -> None:
        """Create the project structure for the specified app name."""
        os.makedirs(f"{app_name}/models", exist_ok=True)
        os.makedirs(f"{app_name}/configurations", exist_ok=True)
        with open(f"{app_name}/starter.py", "w") as f:
            f.write(CLIConstants.STARTER_TEMPLATE)


class OrchestratorCommand(BaseCommand):
    """Handles orchestrator management commands."""

    def execute(self, args: argparse.Namespace) -> None:
        """Execute orchestrator command."""
        try:
            command_args = self._prepare_command_args(args)
            response = self.client.send_command(args.command[0], command_args)

            if response:
                output_format = getattr(args, "format", "table")
                output = self.formatter.format_response(
                    args.command[0], response, output_format
                )
                print(output)
            else:
                print(
                    f"Error: Cannot connect to ZMQ address {self.client.zmq_address}. "
                    "Is the orchestrator running with command interface enabled?"
                )

        except RuntimeError as e:
            print(f"Error: {e}")

    def _prepare_command_args(self, args: argparse.Namespace) -> List[str]:
        """Prepare command arguments based on the command type."""
        if not hasattr(args, "command") or not args.command:
            return []

        command = args.command[0]

        # Handle agent-specific commands
        if hasattr(args, "agent_name") and args.agent_name:
            return [args.agent_name]

        # Handle history commands with parameters
        if command in ["history", "history-stats"]:
            params = {}
            for param in ["last", "agent", "event_name", "after_seq"]:
                if hasattr(args, param) and getattr(args, param) is not None:
                    params[param] = getattr(args, param)

            return [json.dumps(params)] if params else []

        # Return additional arguments if any
        return args.command[1:] if len(args.command) > 1 else []


class StatsCommand(BaseCommand):
    """Handles real-time stats monitoring."""

    def __init__(
        self,
        client: CommandClient,
        formatter: "OutputFormatter",
        interval: float = CLIConstants.DEFAULT_STATS_INTERVAL,
    ):
        super().__init__(client, formatter)
        self.interval = interval

    def execute(self, args: argparse.Namespace) -> None:
        """Display real-time stats of all agents."""
        self.interval = getattr(args, "interval", CLIConstants.DEFAULT_STATS_INTERVAL)

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
                self._display_stats_iteration()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")

    def _display_stats_iteration(self) -> None:
        """Display one iteration of stats."""
        # Clear screen
        os.system("clear" if os.name == "posix" else "cls")

        print("AGENT STATS - Press Ctrl+C to stop")
        print("=" * 80)

        try:
            response = self.client.send_command("stats")

            if response:
                if response.get("status") == "success":
                    output = self.formatter.format_stats_output(
                        response.get("data", {})
                    )
                    print(output)
                else:
                    print(f"Error: {response.get('message', 'Unknown error')}")
            else:
                print(f"Error: Cannot connect to ZMQ address {self.client.zmq_address}")
                print("Is the orchestrator running with command interface enabled?")

        except Exception as e:
            print(f"Error: {e}")


class CommandRouter:
    """Routes commands to appropriate command handlers."""

    def __init__(self, client: CommandClient, formatter: "OutputFormatter"):
        self.client = client
        self.formatter = formatter
        self._commands = {
            "create": ProjectCommand(client, formatter),
            "orchestrator": OrchestratorCommand(client, formatter),
            "stats": StatsCommand(client, formatter),
        }

    def route_command(self, args: argparse.Namespace) -> None:
        """Route the command to the appropriate handler."""
        command_type = self._determine_command_type(args)

        if command_type in self._commands:
            self._commands[command_type].execute(args)
        else:
            raise ValueError(f"Unknown command type: {command_type}")

    def _determine_command_type(self, args: argparse.Namespace) -> str:
        """Determine the type of command based on the arguments."""
        if hasattr(args, "app_name"):
            return "create"
        elif hasattr(args, "interval"):  # stats command
            return "stats"
        else:
            return "orchestrator"


class ArgumentParser:
    """Handles CLI argument parsing."""

    @staticmethod
    def create_parser() -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(description="PyOrchestrate CLI")
        parser.add_argument(
            "--version",
            "-v",
            action="version",
            version=f"PyOrchestrate version {CLIConstants.VERSION}",
        )

        subparsers = parser.add_subparsers(dest="command")

        # Project creation command
        ArgumentParser._add_create_command(subparsers)

        # Orchestrator commands
        ArgumentParser._add_orchestrator_commands(subparsers)

        # Stats command
        ArgumentParser._add_stats_command(subparsers)

        return parser

    @staticmethod
    def _add_create_command(subparsers) -> None:
        """Add the create command parser."""
        create_parser = subparsers.add_parser(
            "create", help="Create a new project structure with the specified app name"
        )
        create_parser.add_argument("app_name", help="Name of the app to create")

    @staticmethod
    def _add_orchestrator_commands(subparsers) -> None:
        """Add orchestrator management command parsers."""
        orchestrator_commands = [
            ("ps", "List all agents and their status"),
            ("status", "Get orchestrator or agent status"),
            ("dependencies", "Show agent dependencies"),
            ("start", "Start a specific agent"),
            ("stop", "Stop a specific agent"),
            ("commands", "List allowed commands for this orchestrator"),
            ("shutdown", "Shutdown the orchestrator gracefully"),
            ("history", "Get event history with optional filtering"),
            ("history-stats", "Get aggregated event statistics"),
        ]

        for cmd_name, cmd_help in orchestrator_commands:
            cmd_parser = subparsers.add_parser(cmd_name, help=cmd_help)
            cmd_parser.add_argument(
                "--socket",
                default=CLIConstants.DEFAULT_ZMQ_ADDRESS,
                help=f"ZeroMQ address (default: {CLIConstants.DEFAULT_ZMQ_ADDRESS})",
            )

            if cmd_name in ["status", "stop", "start"]:
                cmd_parser.add_argument("agent_name", nargs="?", help="Agent name")
            elif cmd_name in ["history", "history-stats"]:
                cmd_parser.add_argument(
                    "--last", type=int, help="Number of last events"
                )
                cmd_parser.add_argument(
                    "--agent", type=str, help="Filter by agent name"
                )
                cmd_parser.add_argument("--type", type=str, help="Filter by event type")
                cmd_parser.add_argument(
                    "--after-seq", type=int, help="Filter by sequence number"
                )

            cmd_parser.add_argument(
                "--format",
                choices=["table", "json"],
                default="table",
                help="Output format",
            )

    @staticmethod
    def _add_stats_command(subparsers) -> None:
        """Add the stats command parser."""
        stats_parser = subparsers.add_parser(
            "stats", help="Display real-time stats of all agents (like docker stats)"
        )
        stats_parser.add_argument(
            "--socket",
            default=CLIConstants.DEFAULT_ZMQ_ADDRESS,
            help=f"ZeroMQ address (default: {CLIConstants.DEFAULT_ZMQ_ADDRESS})",
        )
        stats_parser.add_argument(
            "--interval",
            type=float,
            default=CLIConstants.DEFAULT_STATS_INTERVAL,
            help=f"Refresh interval in seconds (default: {CLIConstants.DEFAULT_STATS_INTERVAL})",
        )

    @staticmethod
    def prepare_command_from_args(args: argparse.Namespace) -> None:
        """Prepare command list from parsed arguments."""
        if hasattr(args, "socket"):
            # This is an orchestrator command
            command_name = args.command

            if hasattr(args, "agent_name") and args.agent_name:
                args.command = [command_name, args.agent_name]
            elif command_name in ["history", "history-stats"]:
                # Prepare parameters for history commands
                params = {}
                for param in ["last", "agent", "event_name"]:
                    if hasattr(args, param) and getattr(args, param) is not None:
                        params[param] = getattr(args, param)
                if hasattr(args, "after_seq") and args.after_seq is not None:
                    params["after_seq"] = args.after_seq

                args.command = (
                    [command_name, json.dumps(params)] if params else [command_name]
                )
            else:
                args.command = [command_name]


class CLIApplication:
    """Main CLI application class."""

    def __init__(self):
        self.parser = ArgumentParser.create_parser()
        self.formatter = OutputFormatter()

    def run(self, argv: Optional[List[str]] = None) -> None:
        """Run the CLI application."""
        args = self.parser.parse_args(argv)

        if not hasattr(args, "command") or args.command is None:
            self.parser.print_help()
            return

        try:
            # Prepare command arguments
            ArgumentParser.prepare_command_from_args(args)

            # Create client with appropriate socket path
            socket_path = getattr(args, "socket", CLIConstants.DEFAULT_ZMQ_ADDRESS)
            client = CommandClient(socket_path)

            # Route and execute command
            router = CommandRouter(client, self.formatter)
            router.route_command(args)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


class OutputFormatter:
    """Handles formatting of CLI output."""

    @staticmethod
    def format_response(
        command: str, response_data: Dict[str, Any], output_format: str = "table"
    ) -> str:
        """Format response based on command type and output format."""
        if output_format == "json":
            if response_data.get("status") == "success":
                return json.dumps(
                    response_data.get("data", {}), indent=2, ensure_ascii=False
                )
            else:
                return json.dumps(response_data, indent=2, ensure_ascii=False)

        return OutputFormatter._format_table_output(command, response_data)

    @staticmethod
    def _format_table_output(command: str, response_data: Dict[str, Any]) -> str:
        """Format response as human-readable table output."""
        if response_data.get("status") != "success":
            return f"Error: {response_data.get('error', 'Unknown error')}"

        data = response_data.get("data", {})

        if command in ["ps"]:
            return OutputFormatter._format_agent_list(data)
        elif command == "status":
            return OutputFormatter._format_status(data)
        elif command == "dependencies":
            return OutputFormatter._format_dependencies(data)
        elif command == "commands":
            return OutputFormatter._format_allowed_commands(data)
        elif command in ["start", "stop"]:
            return response_data.get("message", "Operation completed")
        elif command == "history":
            return OutputFormatter._format_history(data)
        elif command == "history-stats":
            return OutputFormatter._format_history_stats(data)
        else:
            return json.dumps(response_data, indent=2)

    @staticmethod
    def _format_agent_list(data: Dict[str, Any]) -> str:
        """Format agent list output."""
        output = []
        agents = data.get("agents", [])

        output.append(
            f"Orchestrator Status: {data.get('running_count', 0)}/{data.get('max_workers', 0)} agents running"
        )

        if data.get("waiting_count", 0) > 0:
            output.append(f"Waiting in queue: {data.get('waiting_count', 0)}")

        output.append("")

        if agents:
            output.append(f"{'Name':<20} {'Status':<10} {'Started':<8} {'In Queue':<8}")
            output.append("-" * 50)
            for agent in agents:
                status = "ALIVE" if agent.get("alive") else "DEAD"
                started = "YES" if agent.get("started") else "NO"
                queued = "YES" if agent.get("in_queue") else "NO"
                output.append(
                    f"{agent['agent_name']:<20} {status:<10} {started:<8} {queued:<8}"
                )
        else:
            output.append("No agents registered")

        return "\n".join(output)

    @staticmethod
    def _format_status(data: Dict[str, Any]) -> str:
        """Format status output."""
        output = []

        if "name" in data:  # Agent status
            output.append(f"Agent: {data['name']}")
            output.append(f"Alive: {data.get('alive', False)}")
            output.append(f"Started: {data.get('started', False)}")
            output.append(f"In Queue: {data.get('in_queue', False)}")
            if data.get("dependencies"):
                output.append(f"Dependencies: {', '.join(data['dependencies'])}")
        else:  # Orchestrator status
            output.append(f"Total Agents: {data.get('total_agents', 0)}")
            output.append(f"Running Agents: {data.get('running_agents', 0)}")
            output.append(f"Max Workers: {data.get('max_workers', 0)}")
            output.append(f"Waiting Agents: {data.get('waiting_agents', 0)}")
            output.append(
                f"Command Interface: {'Enabled' if data.get('command_interface_enabled') else 'Disabled'}"
            )
            if data.get("command_socket_path"):
                output.append(f"Socket Path: {data['command_socket_path']}")

        return "\n".join(output)

    @staticmethod
    def _format_dependencies(data: Dict[str, Any]) -> str:
        """Format dependencies output."""
        deps = data.get("dependencies", {})

        if deps:
            output = ["Agent Dependencies:"]
            for agent, deps_list in deps.items():
                if deps_list:
                    output.append(f"  {agent} -> {', '.join(deps_list)}")
            return "\n".join(output)
        else:
            return "No dependencies configured"

    @staticmethod
    def _format_allowed_commands(data: Dict[str, Any]) -> str:
        """Format allowed commands output."""
        output = []
        allowed = data.get("allowed_commands", [])
        total_available = data.get("total_available_commands", [])
        restrictions_active = data.get("restrictions_active", False)
        restricted = data.get("restricted_commands", [])

        if restrictions_active:
            output.append("🔒 COMMAND RESTRICTIONS ACTIVE")
            output.append("")
            output.append(f"Allowed commands ({len(allowed)}):")
            for cmd in allowed:
                output.append(f"  ✅ {cmd}")

            if restricted:
                output.append("")
                output.append(f"Restricted commands ({len(restricted)}):")
                for cmd in restricted:
                    output.append(f"  ❌ {cmd}")
        else:
            output.append("🔓 ALL COMMANDS ALLOWED")
            output.append("")
            output.append(f"Available commands ({len(total_available)}):")
            for cmd in total_available:
                output.append(f"  ✅ {cmd}")

        return "\n".join(output)

    @staticmethod
    def _format_history(data: Dict[str, Any]) -> str:
        """Format history output."""
        output = []
        events = data.get("events", [])
        count = data.get("count", 0)
        filters = data.get("filters", {})
        capacity_info = data.get("capacity_info", {})

        output.append(f"=== Event History ({count} events) ===")

        if filters:
            filter_parts = []
            if filters.get("agent"):
                filter_parts.append(f"agent={filters['agent']}")
            if filters.get("event_name"):
                filter_parts.append(f"type={filters['type']}")
            if filters.get("last"):
                filter_parts.append(f"last={filters['last']}")
            if filters.get("after_seq"):
                filter_parts.append(f"after_seq={filters['after_seq']}")

            if filter_parts:
                output.append(f"Filters: {', '.join(filter_parts)}")

        output.append(
            f"Buffer: {capacity_info.get('current_size', 0)}/{capacity_info.get('capacity', 0)} events"
        )
        output.append("")

        if events:
            output.append(
                f"{'SEQ':<6} {'TIME':<19} {'CATEGORY':<12} {'EVENT NAME':<20} {'AGENT':<15} {'SEV':<5}"
            )
            output.append("-" * 80)
            for event in events:
                timestamp = event.get("timestamp", "")[:19]
                category = event.get("category", "")[:11]
                event_type = event.get("event_name", "")[:19]
                agent = (event.get("agent") or "")[:14]
                severity = event.get("severity", "")[:4]
                seq = event.get("seq", 0)

                output.append(
                    f"{seq:<6} {timestamp:<19} {category:<12} {event_type:<20} {agent:<15} {severity:<5}"
                )
        else:
            output.append("No events found")

        return "\n".join(output)

    @staticmethod
    def _format_history_stats(data: Dict[str, Any]) -> str:
        """Format history stats output."""
        output = []
        statistics = data.get("statistics", {})
        capacity_info = data.get("capacity_info", {})
        agent_filter = data.get("agent_filter")
        timestamp = data.get("timestamp", "")

        output.append("=== Event Statistics ===")
        output.append(f"Timestamp: {timestamp}")
        if agent_filter:
            output.append(f"Agent Filter: {agent_filter}")
        output.append(
            f"Buffer: {capacity_info.get('current_size', 0)}/{capacity_info.get('capacity', 0)} events"
        )
        output.append(f"Total Events: {capacity_info.get('total_events', 0)}")
        output.append("")

        by_type = statistics.get("by_type", {})
        if by_type:
            output.append("Event Type Breakdown:")
            sorted_events = sorted(by_type.items(), key=lambda x: x[1], reverse=True)
            for event_type, count in sorted_events:
                output.append(f"  {event_type:<25} {count:>6}")
        else:
            output.append("No event statistics available")

        return "\n".join(output)

    @staticmethod
    def format_stats_output(data: Dict[str, Any]) -> str:
        """Format stats output for real-time monitoring."""
        output = []

        # Orchestrator info
        orch_data = data.get("orchestrator", {})
        timestamp = data.get("timestamp", "")

        output.append(f"Timestamp: {timestamp}")
        output.append(
            f"Running: {orch_data.get('running_agents', 0)}/{orch_data.get('max_workers', 0)} agents"
        )
        output.append(f"Waiting: {orch_data.get('waiting_agents', 0)} agents")
        output.append("")

        # Agent stats table
        agents = data.get("agents", [])
        if agents:
            output.append(
                f"{'NAME':<20} {'STATUS':<8} {'PID':<8} {'CPU %':<8} {'MEM MB':<10} {'MEM %':<8} {'THREADS':<8} {'UPTIME':<12}"
            )
            output.append("-" * 90)

            for agent in agents:
                name = agent.get("name", "")[:19]
                status = "ALIVE" if agent.get("alive") else "DEAD"
                pid = str(agent.get("pid", "N/A"))[:7]
                cpu = str(agent.get("cpu_percent", "N/A"))[:7]
                mem_mb = str(agent.get("memory_mb", "N/A"))[:9]
                mem_pct = str(agent.get("memory_percent", "N/A"))[:7]
                threads = str(agent.get("threads", "N/A"))[:7]
                uptime = str(agent.get("uptime", "N/A"))[:11]

                output.append(
                    f"{name:<20} {status:<8} {pid:<8} {cpu:<8} {mem_mb:<10} {mem_pct:<8} {threads:<8} {uptime:<12}"
                )
        else:
            output.append("No agents registered")

        return "\n".join(output)


def main() -> None:
    """Entry point for the CLI application."""
    app = CLIApplication()
    app.run()


if __name__ == "__main__":
    main()
