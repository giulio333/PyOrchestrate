from enum import Enum


class OrchestratorEvent(Enum):
    """
    Enum of events that the orchestrator can emit.
    """
    AGENT_STARTED = "agent_started"
    """Event emitted when an agent is started. Take the agent name as argument (`agent_name`)."""
    AGENT_TERMINATED = "agent_terminated"
    """Event emitted when an agent is terminated. Take the agent name as argument (`agent_name`)."""
    ALL_AGENTS_COMPLETED = "all_agents_completed"
    """Event emitted when all agents are completed. Take no arguments."""
