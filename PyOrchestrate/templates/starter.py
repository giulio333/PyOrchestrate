# starter.py template

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
