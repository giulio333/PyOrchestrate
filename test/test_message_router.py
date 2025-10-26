"""
Unit tests for MessageRouter.

Tests the message routing logic including event conversion, stale message filtering,
and thread-safe termination tracking.
"""

import unittest
from unittest.mock import MagicMock, call
import threading
import time

from PyOrchestrate.core.orchestrator.message_router import MessageRouter
from PyOrchestrate.core.utilities.messaging import ServiceMessage, MessageChannel
from PyOrchestrate.core.utilities.event import OrchestratorEvent, AgentEvent


class TestMessageRouter(unittest.TestCase):
    """Test suite for MessageRouter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.event_manager = MagicMock()
        self.message_channel = MessageChannel("process")
        self.logger = MagicMock()
        self.router = MessageRouter(
            self.event_manager, self.message_channel, self.logger
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if self.router.is_running():
            self.router.stop()
        self.message_channel.close()

    def test_initialization(self):
        """Test MessageRouter initialization."""
        self.assertIsNotNone(self.router.event_manager)
        self.assertIsNotNone(self.router.message_channel)
        self.assertIsNotNone(self.router.logger)
        self.assertEqual(len(self.router._terminated_agents), 0)
        self.assertFalse(self.router.is_running())

    def test_route_agent_started_message(self):
        """Test routing AGENT_START message."""
        msg = ServiceMessage.create_status(
            sender="test_agent",
            status="started",
            event_name=AgentEvent.AGENT_START.value,
        )

        self.router.route_agent_message(msg)

        self.event_manager.emit.assert_called_once_with(
            OrchestratorEvent.AGENT_STARTED, agent_name="test_agent"
        )

    def test_route_agent_ready_message(self):
        """Test routing AGENT_READY message."""
        msg = ServiceMessage.create_status(
            sender="test_agent", status="ready", event_name=AgentEvent.AGENT_READY.value
        )

        self.router.route_agent_message(msg)

        self.event_manager.emit.assert_called_once_with(
            OrchestratorEvent.AGENT_READY, agent_name="test_agent"
        )

    def test_route_agent_close_message(self):
        """Test routing AGENT_CLOSE message marks agent as terminated."""
        msg = ServiceMessage.create_status(
            sender="test_agent",
            status="closed",
            event_name=AgentEvent.AGENT_CLOSE.value,
        )

        self.router.route_agent_message(msg)

        # Should emit AGENT_TERMINATED event
        self.event_manager.emit.assert_called_once_with(
            OrchestratorEvent.AGENT_TERMINATED, agent_name="test_agent"
        )

        # Should mark agent as terminated
        self.assertTrue(self.router.is_agent_terminated("test_agent"))

    def test_route_agent_heartbeat_message(self):
        """Test routing AGENT_HEARTBEAT message from active agent."""
        msg = ServiceMessage.create_status(
            sender="test_agent",
            status="heartbeat",
            event_name=AgentEvent.AGENT_HEARTBEAT.value,
        )

        self.router.route_agent_message(msg)

        self.event_manager.emit.assert_called_once_with(
            OrchestratorEvent.AGENT_HEARTBEAT, agent_name="test_agent"
        )

    def test_filter_stale_heartbeat_from_terminated_agent(self):
        """Test that heartbeats from terminated agents are filtered."""
        # Mark agent as terminated
        self.router.mark_agent_terminated("test_agent")

        # Send heartbeat message
        msg = ServiceMessage.create_status(
            sender="test_agent",
            status="heartbeat",
            event_name=AgentEvent.AGENT_HEARTBEAT.value,
        )

        self.router.route_agent_message(msg)

        # Should NOT emit heartbeat event
        self.event_manager.emit.assert_not_called()

        # Should log debug message about filtering
        self.logger.debug.assert_called()

    def test_route_agent_error_message(self):
        """Test routing ERROR message."""
        msg = ServiceMessage.create_status(
            sender="test_agent", status="error", event_name="ERROR", error="Test error"
        )

        self.router.route_agent_message(msg)

        self.event_manager.emit.assert_called_once_with(
            OrchestratorEvent.AGENT_ERROR,
            agent_name="test_agent",
            error_message="Test error",
        )
        self.logger.error.assert_called_once()

    def test_route_non_status_message_ignored(self):
        """Test that non-STATUS messages are ignored."""
        msg = ServiceMessage.create_command(
            sender="test_agent", command="test", request_id="123"
        )

        self.router.route_agent_message(msg)

        # Should not emit any events
        self.event_manager.emit.assert_not_called()

        # Should log warning
        self.logger.warning.assert_called_once()

    def test_route_unknown_event_logs_warning(self):
        """Test that unknown event types log a warning."""
        msg = ServiceMessage.create_status(
            sender="test_agent", status="unknown", event_name="UNKNOWN_EVENT"
        )

        self.router.route_agent_message(msg)

        # Should not emit any events
        self.event_manager.emit.assert_not_called()

        # Should log warning about unknown event
        self.logger.warning.assert_called()

    def test_mark_agent_terminated(self):
        """Test marking an agent as terminated."""
        self.assertFalse(self.router.is_agent_terminated("agent1"))

        self.router.mark_agent_terminated("agent1")

        self.assertTrue(self.router.is_agent_terminated("agent1"))

    def test_is_agent_terminated_false_for_active_agent(self):
        """Test that active agents are not marked as terminated."""
        self.assertFalse(self.router.is_agent_terminated("active_agent"))

    def test_reset_termination_state(self):
        """Test resetting termination state for an agent."""
        # Mark agent as terminated
        self.router.mark_agent_terminated("agent1")
        self.assertTrue(self.router.is_agent_terminated("agent1"))

        # Reset termination state
        self.router.reset_termination_state("agent1")
        self.assertFalse(self.router.is_agent_terminated("agent1"))

    def test_get_terminated_agents(self):
        """Test getting copy of terminated agents set."""
        self.router.mark_agent_terminated("agent1")
        self.router.mark_agent_terminated("agent2")

        terminated = self.router.get_terminated_agents()

        self.assertEqual(len(terminated), 2)
        self.assertIn("agent1", terminated)
        self.assertIn("agent2", terminated)

        # Verify it's a copy (modifying it doesn't affect internal state)
        terminated.add("agent3")
        self.assertFalse(self.router.is_agent_terminated("agent3"))

    def test_thread_safe_termination_tracking(self):
        """Test that termination tracking is thread-safe."""

        def mark_terminated(agent_name):
            for _ in range(100):
                self.router.mark_agent_terminated(agent_name)

        def check_terminated(agent_name, results):
            for _ in range(100):
                results.append(self.router.is_agent_terminated(agent_name))

        # Create threads
        results = []
        threads = [
            threading.Thread(target=mark_terminated, args=("agent1",)),
            threading.Thread(target=check_terminated, args=("agent1", results)),
        ]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Verify agent is marked as terminated
        self.assertTrue(self.router.is_agent_terminated("agent1"))

    def test_concurrent_mark_and_reset(self):
        """Test concurrent marking and resetting of termination state."""

        def mark_and_reset():
            for _ in range(50):
                self.router.mark_agent_terminated("agent1")
                time.sleep(0.001)  # Small delay
                self.router.reset_termination_state("agent1")

        threads = [threading.Thread(target=mark_and_reset) for _ in range(3)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should complete without errors (thread-safety verified)

    def test_multiple_agents_termination_tracking(self):
        """Test tracking termination for multiple agents."""
        agents = ["agent1", "agent2", "agent3", "agent4", "agent5"]

        # Mark some agents as terminated
        for agent in agents[:3]:
            self.router.mark_agent_terminated(agent)

        # Verify correct termination states
        for agent in agents[:3]:
            self.assertTrue(self.router.is_agent_terminated(agent))

        for agent in agents[3:]:
            self.assertFalse(self.router.is_agent_terminated(agent))

    def test_heartbeat_filtering_sequence(self):
        """Test complete sequence of heartbeat filtering."""
        # Agent sends heartbeat - should be processed
        msg1 = ServiceMessage.create_status(
            sender="agent1",
            status="heartbeat",
            event_name=AgentEvent.AGENT_HEARTBEAT.value,
        )
        self.router.route_agent_message(msg1)
        self.assertEqual(self.event_manager.emit.call_count, 1)

        # Agent closes - should mark as terminated
        msg2 = ServiceMessage.create_status(
            sender="agent1", status="closed", event_name=AgentEvent.AGENT_CLOSE.value
        )
        self.router.route_agent_message(msg2)
        self.assertEqual(self.event_manager.emit.call_count, 2)

        # Stale heartbeat arrives - should be filtered
        msg3 = ServiceMessage.create_status(
            sender="agent1",
            status="heartbeat",
            event_name=AgentEvent.AGENT_HEARTBEAT.value,
        )
        self.router.route_agent_message(msg3)
        # Still 2 calls (heartbeat was filtered)
        self.assertEqual(self.event_manager.emit.call_count, 2)

    def test_start_and_stop(self):
        """Test starting and stopping the message router."""
        self.assertFalse(self.router.is_running())

        self.router.start()
        self.assertTrue(self.router.is_running())

        self.router.stop()
        self.assertFalse(self.router.is_running())

    def test_start_already_started(self):
        """Test starting an already started router."""
        self.router.start()
        self.assertTrue(self.router.is_running())

        # Starting again should log warning but not fail
        self.router.start()
        self.assertTrue(self.router.is_running())

        self.router.stop()

    def test_stop_not_started(self):
        """Test stopping a router that was never started."""
        self.assertFalse(self.router.is_running())
        # Should not raise exception
        self.router.stop()
        self.assertFalse(self.router.is_running())


if __name__ == "__main__":
    unittest.main()
