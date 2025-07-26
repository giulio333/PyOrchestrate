import argparse
import os
import socket


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

    # Initialize Orchestrator
    orchestrator = Orchestrator()

    # Register Agents
    # orchestrator.register_agent(YouAgent)

    # Start Orchestrator
    orchestrator.start()

    # Join Agents
    orchestrator.join()
"""


def start_command(args: argparse.Namespace) -> None:
    """Handle the ``start`` subcommand."""
    create_project_structure(args.app_name)
    print(f"Project structure for '{args.app_name}' created successfully.")


def send_command(args: argparse.Namespace) -> None:
    """Send a command to a running orchestrator via UNIX socket."""
    cmd = " ".join(args.command)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(args.socket)
        s.sendall(cmd.encode())
        resp = s.recv(4096).decode().strip()
    print(resp)


def main() -> None:
    parser = argparse.ArgumentParser(description="PyOrchestrate CLI")
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="PyOrchestrate version 0.2.0",
    )

    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser(
        "start", help="Create a new project structure with the specified app name"
    )
    start_parser.add_argument("app_name", help="Name of the app to create")
    start_parser.set_defaults(func=start_command)

    send_parser = subparsers.add_parser(
        "send", help="Send a command to a running orchestrator"
    )
    send_parser.add_argument("socket", help="Path to orchestrator socket")
    send_parser.add_argument("command", nargs=argparse.REMAINDER)
    send_parser.set_defaults(func=send_command)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
