"""Worker pool and agent scheduling queue management."""

from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyOrchestrate.core.orchestrator.lifecycle_manager import AgentLifecycleManager


class WorkerPoolScheduler:
    """
    Manages worker pool and agent scheduling queue.
    
    This class handles:
    - Enforcing max_workers limit
    - Queueing agents when limit is reached
    - Automatically scheduling agents from queue when slots free up
    - Tracking running agent count
    
    Example:
        >>> scheduler = WorkerPoolScheduler(max_workers=5, lifecycle_manager, logger)
        >>> scheduler.start_agent("agent1")  # Starts immediately if slot available
        >>> scheduler.start_agent("agent2")  # Queued if at capacity
        >>> scheduler.on_agent_terminated("agent1")  # Starts next queued agent
    """
    
    def __init__(
        self,
        max_workers: int,
        lifecycle_manager: "AgentLifecycleManager",
        logger
    ):
        """
        Initialize the worker pool scheduler.
        
        Args:
            max_workers: Maximum number of concurrently running agents
            lifecycle_manager: Agent lifecycle manager for starting agents
            logger: Logger instance
        """
        self.max_workers = max_workers
        self.lifecycle_manager = lifecycle_manager
        self.logger = logger
        
        self._running_agents = 0
        self._started_agents: set[str] = set()
        self._waiting_queue: deque[str] = deque()
    
    def can_start_agent(self) -> bool:
        """
        Check if there's capacity to start a new agent.
        
        Returns:
            bool: True if running_agents < max_workers, False otherwise
        """
        return self._running_agents < self.max_workers
    
    def start_agent(self, agent_name: str) -> bool:
        """
        Start an agent immediately or queue it if at capacity.
        
        Args:
            agent_name: Name of the agent to start
            
        Returns:
            bool: True if agent started, False if queued
        """
        if not self.can_start_agent():
            self.logger.warning(
                f"Max workers ({self.max_workers}) reached. "
                f"Queueing agent '{agent_name}'"
            )
            self._waiting_queue.append(agent_name)
            return False
        
        # Start agent via lifecycle manager
        success = self.lifecycle_manager.start_agent(agent_name)
        
        if success:
            self._running_agents += 1
            self._started_agents.add(agent_name)
            self.logger.info(
                f"Agent '{agent_name}' started "
                f"({self._running_agents}/{self.max_workers} slots used)"
            )
        
        return success
    
    def on_agent_terminated(self, agent_name: str) -> None:
        """
        Callback when an agent terminates.
        
        Decrements running count and starts next queued agent if available.
        
        Args:
            agent_name: Name of the terminated agent
        """
        if agent_name not in self._started_agents:
            self.logger.debug(
                f"Agent '{agent_name}' terminated but was never started (timeout?)"
            )
            return
        
        self._running_agents -= 1
        self._started_agents.remove(agent_name)
        
        self.logger.info(
            f"Agent '{agent_name}' terminated "
            f"({self._running_agents}/{self.max_workers} slots used)"
        )
        
        # Try to start next agent from queue
        self._start_next_queued_agent()
    
    def _start_next_queued_agent(self) -> None:
        """Start the next agent from the waiting queue if available."""
        if not self._waiting_queue:
            return
        
        if not self.can_start_agent():
            self.logger.debug("No free slots to start queued agents")
            return
        
        agent_name = self._waiting_queue.popleft()
        self.logger.info(f"Starting queued agent '{agent_name}'")
        
        success = self.lifecycle_manager.start_agent(agent_name)
        
        if success:
            self._running_agents += 1
            self._started_agents.add(agent_name)
    
    @property
    def all_finished(self) -> bool:
        """
        Check if all agents have finished (none running, none queued).
        
        Returns:
            bool: True if no agents running and queue is empty
        """
        return self._running_agents == 0 and len(self._waiting_queue) == 0
    
    @property
    def queue_size(self) -> int:
        """
        Get current size of the waiting queue.
        
        Returns:
            int: Number of agents waiting in queue
        """
        return len(self._waiting_queue)
    
    @property
    def running_count(self) -> int:
        """
        Get number of currently running agents.
        
        Returns:
            int: Number of agents currently running
        """
        return self._running_agents
    
    def get_stats(self) -> dict:
        """
        Get current scheduler statistics.
        
        Returns:
            dict: Statistics including running count, queue size, capacity
        """
        return {
            "running": self._running_agents,
            "queued": len(self._waiting_queue),
            "max_workers": self.max_workers,
            "capacity_used": f"{self._running_agents}/{self.max_workers}",
            "started_agents": list(self._started_agents)
        }
