import unittest
from unittest.mock import MagicMock, patch
import sys, os

from PyOrchestrate.core.utilities.event_manager import EventManager
from PyOrchestrate.core.agent.looping_agent import (
    LoopingAgent,
)
from PyOrchestrate.core.utilities.validation import ConfigValidationError

from PyOrchestrate.core.base.utilities import LoggerConfig


class TestLoopingAgentConfig(unittest.TestCase):
    def test_default_values(self):
        """Test default configuration values"""
        config = LoopingAgent.Config()
        self.assertEqual(config.limit, -1)

    def test_custom_values(self):
        """Test custom configuration values"""
        config = LoopingAgent.Config(limit=10)
        self.assertEqual(config.limit, 10)

    def test_invalid_limit(self):
        """Test validation with invalid limit"""
        config = LoopingAgent.Config(limit=-2)
        with self.assertRaises(ConfigValidationError):
            config._validate()


class TestLoopingAgent(unittest.TestCase):

    class ConcreteLoopingAgent(LoopingAgent):

        def cycle(self):
            pass

        def _info(self):
            super()._info()

    def setUp(self):

        self.event_manager = EventManager()
        self.state_events = LoopingAgent.StateEvents(
            MagicMock(), MagicMock(), MagicMock()
        )
        self.control_events = LoopingAgent.ControlEvents(
            MagicMock(), MagicMock(), MagicMock()
        )
        self.config = LoopingAgent.Config(limit=5)
        self.plugin = LoopingAgent.Plugin()

        # Initialize test agent object
        self.agent = self.ConcreteLoopingAgent(
            name="test_looping_agent",
            config=self.config,
            plugin=self.plugin,
            a_type="process",
            state_events=self.state_events,
            control_events=self.control_events,
            custom_attr="custom_value",
            event_manager=self.event_manager,
        )

    def test_initialization(self):
        """Test agent initialization"""

        # Check agent attributes
        self.assertEqual(self.agent.name, "test_looping_agent")
        self.assertEqual(self.agent.a_type, "process")
        self.assertEqual(self.agent.config, self.config)
        self.assertEqual(self.agent.custom_attr, "custom_value")  # type:ignore

        # Check agent events
        self.assertEqual(self.agent.state_events, self.state_events)
        self.assertEqual(self.agent.control_events, self.control_events)
        self.assertEqual(
            self.agent.state_events.ready_event, self.state_events.ready_event
        )
        self.assertEqual(
            self.agent.state_events.close_event, self.state_events.close_event
        )
        self.assertEqual(
            self.agent.control_events.setup_event, self.control_events.setup_event
        )
        self.assertEqual(
            self.agent.control_events.execute_event, self.control_events.execute_event
        )
        self.assertEqual(
            self.agent.control_events.stop_event, self.control_events.stop_event
        )

        # Default logger configuration
        self.assertEqual(self.agent.config.logger_config, LoggerConfig())

    def test_execute_without_limit(self):
        """Test execute with infinite loop"""
        self.config.limit = -1
        self.agent.safe_cycle = MagicMock()  # type:ignore
        self.control_events.stop_event.is_set.side_effect = [False, False, True]
        self.agent.run()
        self.assertEqual(self.agent.safe_cycle.call_count, 2)

    def test_execute_with_limit_early_stop(self):
        """Test execute with limit but stopped early"""
        self.agent.safe_cycle = MagicMock()  # type:ignore
        self.control_events.stop_event.is_set.side_effect = [False, True]
        self.agent.run()
        self.assertEqual(self.agent.safe_cycle.call_count, 1)

    def test_execute_reaches_limit(self):
        """Test execute reaches limit and logs message"""
        self.agent.safe_cycle = MagicMock()  # type:ignore
        self.control_events.stop_event.is_set.return_value = False
        self.agent.run()
        self.assertEqual(self.agent.safe_cycle.call_count, 5)

    def test_inheritance(self):
        """Test inheritance chain"""
        self.assertIsInstance(self.agent, LoopingAgent)
        self.assertTrue(hasattr(self.agent, "cycle"))
        self.assertTrue(hasattr(self.agent, "_info"))
