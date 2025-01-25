import argparse
import os

def create_project_structure(app_name):
    """
    Create the project structure for the specified app name.
    """
    os.makedirs(f"{app_name}/models", exist_ok=True)
    os.makedirs(f"{app_name}/configurations", exist_ok=True)
    with open(f"{app_name}/starter.py", "w") as f:
        f.write(starter_template)

starter_template = """# starter.py template

# Imports
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import BaseAgent

# Define Agents
class MyAgent(BaseAgent):
    def setup(self):
        pass

    def execute(self):
        pass

# Initialize Orchestrator
orchestrator = Orchestrator()

# Register Agents
orchestrator.register_agent(MyAgent, "MyAgent")

# Start Orchestrator
orchestrator.start()

# Join Orchestrator
orchestrator.join()
"""

def main():
    parser = argparse.ArgumentParser(description="PyOrchestrate CLI")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("app_name", help="Name of the app to create", nargs="?")
    parser.add_argument("--version", "-v", action="store_true", help="Show version")

    args = parser.parse_args()

    if args.version:
        print("PyOrchestrate version 1.0.0")
    elif not args.command:
        parser.print_help()
    elif args.command == "start" and args.app_name:
        create_project_structure(args.app_name)
        print(f"Project structure for '{args.app_name}' created successfully.")
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()

if __name__ == "__main__":
    main()
