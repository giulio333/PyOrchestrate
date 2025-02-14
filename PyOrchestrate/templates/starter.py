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

# Register first agent
agent_entry_1 = orchestrator.register_agent(MyAgent, "MyAgent1")

# Register second agent
agent_entry_2 = orchestrator.register_agent(MyAgent, "MyAgent2")

# Start and join orchestrator
orchestrator.start()
orchestrator.join()
