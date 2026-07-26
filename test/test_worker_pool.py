"""Unit tests for WorkerPoolScheduler class."""

import unittest
from unittest.mock import MagicMock, call
from collections import deque

from PyOrchestrate.core.orchestrator.worker_pool import WorkerPoolScheduler
from PyOrchestrate.core.utilities.command_handler import (
    CommandException,
    CommandHandler,
)


class TestWorkerPoolScheduler(unittest.TestCase):
    """Test cases for WorkerPoolScheduler class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_lifecycle_manager = MagicMock()
        self.mock_logger = MagicMock()
        self.scheduler = WorkerPoolScheduler(
            max_workers=3,
            lifecycle_manager=self.mock_lifecycle_manager,
            logger=self.mock_logger,
        )

    def test_initialization(self):
        """Test scheduler initializes with correct values."""
        self.assertEqual(self.scheduler.max_workers, 3)
        self.assertEqual(self.scheduler.running_count, 0)
        self.assertEqual(self.scheduler.queue_size, 0)
        self.assertTrue(self.scheduler.all_finished)

    def test_can_start_agent_with_capacity(self):
        """Test can_start_agent returns True when below max_workers."""
        self.assertTrue(self.scheduler.can_start_agent())

    def test_can_start_agent_at_capacity(self):
        """Test can_start_agent returns False when at max_workers."""
        # Simulate 3 agents running
        self.scheduler._running_agents = 3
        self.assertFalse(self.scheduler.can_start_agent())

    def test_start_agent_success(self):
        """Test starting agent when capacity available."""
        self.mock_lifecycle_manager.start_agent.return_value = True

        result = self.scheduler.start_agent("agent1")

        self.assertTrue(result)
        self.mock_lifecycle_manager.start_agent.assert_called_once_with("agent1")
        self.assertEqual(self.scheduler.running_count, 1)
        self.assertIn("agent1", self.scheduler._started_agents)

    def test_start_agent_failure(self):
        """Test starting agent when lifecycle manager returns False."""
        self.mock_lifecycle_manager.start_agent.return_value = False

        result = self.scheduler.start_agent("agent1")

        self.assertFalse(result)
        self.assertEqual(self.scheduler.running_count, 0)
        self.assertNotIn("agent1", self.scheduler._started_agents)

    def test_start_agent_queued_at_capacity(self):
        """Test agent is queued when max_workers reached."""
        # Fill capacity
        self.scheduler._running_agents = 3

        result = self.scheduler.start_agent("agent4")

        self.assertFalse(result)
        self.assertEqual(self.scheduler.queue_size, 1)
        self.assertEqual(self.scheduler._waiting_queue[0], "agent4")
        self.mock_lifecycle_manager.start_agent.assert_not_called()

    def test_on_agent_terminated_decrements_count(self):
        """Test on_agent_terminated decrements running count."""
        # Setup: agent1 is running
        self.scheduler._running_agents = 1
        self.scheduler._started_agents.add("agent1")

        self.scheduler.on_agent_terminated("agent1")

        self.assertEqual(self.scheduler.running_count, 0)
        self.assertNotIn("agent1", self.scheduler._started_agents)

    def test_on_agent_terminated_starts_queued_agent(self):
        """Test on_agent_terminated starts next queued agent."""
        # Setup: 3 agents running, 1 queued
        self.scheduler._running_agents = 3
        self.scheduler._started_agents = {"agent1", "agent2", "agent3"}
        self.scheduler._waiting_queue.append("agent4")
        self.mock_lifecycle_manager.start_agent.return_value = True

        self.scheduler.on_agent_terminated("agent1")

        # Should have started agent4
        self.mock_lifecycle_manager.start_agent.assert_called_once_with("agent4")
        self.assertEqual(self.scheduler.running_count, 3)  # 2 + 1 new
        self.assertIn("agent4", self.scheduler._started_agents)
        self.assertEqual(self.scheduler.queue_size, 0)

    def test_on_agent_terminated_never_started(self):
        """Test on_agent_terminated with agent that was never started."""
        # Agent not in started_agents (e.g., timed out)
        self.scheduler.on_agent_terminated("agent_unknown")

        # Should not change running count
        self.assertEqual(self.scheduler.running_count, 0)
        self.mock_logger.debug.assert_called()

    def test_all_finished_with_running_agents(self):
        """Test all_finished returns False when agents running."""
        self.scheduler._running_agents = 2
        self.assertFalse(self.scheduler.all_finished)

    def test_all_finished_with_queued_agents(self):
        """Test all_finished returns False when agents queued."""
        self.scheduler._waiting_queue.append("agent1")
        self.assertFalse(self.scheduler.all_finished)

    def test_all_finished_empty(self):
        """Test all_finished returns True when nothing running or queued."""
        self.assertTrue(self.scheduler.all_finished)

    def test_get_stats(self):
        """Test get_stats returns correct information."""
        self.scheduler._running_agents = 2
        self.scheduler._started_agents = {"agent1", "agent2"}
        self.scheduler._waiting_queue.append("agent3")

        stats = self.scheduler.get_stats()

        self.assertEqual(stats["running"], 2)
        self.assertEqual(stats["queued"], 1)
        self.assertEqual(stats["max_workers"], 3)
        self.assertEqual(stats["capacity_used"], "2/3")
        self.assertEqual(set(stats["started_agents"]), {"agent1", "agent2"})

    def test_multiple_agents_queued_fifo(self):
        """Test multiple queued agents are started in FIFO order."""
        # Fill capacity
        self.scheduler._running_agents = 3
        self.scheduler._started_agents = {"agent1", "agent2", "agent3"}

        # Queue multiple agents
        self.scheduler.start_agent("agent4")
        self.scheduler.start_agent("agent5")
        self.scheduler.start_agent("agent6")

        self.assertEqual(self.scheduler.queue_size, 3)

        # Terminate agent1, should start agent4
        self.mock_lifecycle_manager.start_agent.return_value = True
        self.scheduler.on_agent_terminated("agent1")

        self.mock_lifecycle_manager.start_agent.assert_called_with("agent4")
        self.assertEqual(self.scheduler.queue_size, 2)

        # Terminate agent2, should start agent5
        self.scheduler.on_agent_terminated("agent2")

        calls = self.mock_lifecycle_manager.start_agent.call_args_list
        self.assertEqual(calls[-1], call("agent5"))

    def test_queue_properties(self):
        """Test queue_size and running_count properties."""
        self.scheduler._running_agents = 2
        self.scheduler._waiting_queue = deque(["agent3", "agent4"])

        self.assertEqual(self.scheduler.queue_size, 2)
        self.assertEqual(self.scheduler.running_count, 2)

    def test_stop_command_waits_for_termination_before_advancing_queue(self):
        """Stopping an agent must not release its worker slot prematurely."""
        scheduler = WorkerPoolScheduler(
            max_workers=1,
            lifecycle_manager=self.mock_lifecycle_manager,
            logger=self.mock_logger,
        )
        self.mock_lifecycle_manager.start_agent.return_value = True
        scheduler.start_agent("agent1")
        scheduler.start_agent("agent2")

        orchestrator = MagicMock()
        orchestrator.logger = self.mock_logger
        orchestrator.lifecycle_manager = self.mock_lifecycle_manager
        orchestrator.memory.get_agent.return_value = MagicMock()
        orchestrator.worker_pool = scheduler
        handler = CommandHandler(orchestrator, {"stop"})

        result = handler._cmd_stop_agent("agent1")

        self.assertEqual(result["message"], "Stop requested for agent agent1")
        self.mock_lifecycle_manager.stop_agent.assert_called_once_with("agent1")
        self.assertEqual(scheduler.running_count, 1)
        self.assertIn("agent1", scheduler._started_agents)
        self.assertEqual(list(scheduler._waiting_queue), ["agent2"])

        scheduler.on_agent_terminated("agent1")

        self.assertEqual(
            self.mock_lifecycle_manager.start_agent.call_args_list[-1],
            call("agent2"),
        )
        self.assertEqual(scheduler.running_count, 1)
        self.assertNotIn("agent1", scheduler._started_agents)
        self.assertIn("agent2", scheduler._started_agents)
        self.assertEqual(scheduler.queue_size, 0)

    def test_stop_command_preserves_not_found_error(self):
        """A missing agent remains a 404 instead of being wrapped as a 500."""
        orchestrator = MagicMock()
        orchestrator.logger = self.mock_logger
        orchestrator.memory.get_agent.return_value = None
        handler = CommandHandler(orchestrator, {"stop"})

        with self.assertRaises(CommandException) as context:
            handler._cmd_stop_agent("missing")

        self.assertEqual(context.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
