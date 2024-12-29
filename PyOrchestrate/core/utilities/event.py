from enum import Enum


class OrchestratorEvent(Enum):
    """
    Enum of events that the orchestrator can emit.
    """
    AGENT_STARTED = "agent_started"
    AGENT_TERMINATED = "agent_terminated"
    ALL_AGENTS_COMPLETED = "all_agents_completed"
