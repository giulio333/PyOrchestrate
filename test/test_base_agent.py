import unittest
import sys
import os
from unittest.mock import MagicMock, patch

from PyOrchestrate.core.utilities.event_manager import EventManager
from PyOrchestrate.core.agent.base_agent import (
    BaseAgent,
    ValidationError,
)
from PyOrchestrate.core.base.utilities import LoggerConfig
from PyOrchestrate.core.utilities.event import AgentEvent  # nuovo import


class MyBaseAgent(BaseAgent):

    def execute(self):
        super().execute()


class TestBaseAgentConfig(unittest.TestCase):
    def test_default_values(self):
        """Test default configuration values"""
        config = BaseAgent.Config()
        self.assertEqual(config.logger_config, LoggerConfig())

    def test_custom_values(self):
        """Test custom configuration values"""
        custom_logger_config = LoggerConfig(level="DEBUG")
        custom_value = "custom_value"
        config = BaseAgent.Config(
            logger_config=custom_logger_config, custom_value=custom_value
        )
        self.assertEqual(config.logger_config, custom_logger_config)
        self.assertEqual(config.custom_value, custom_value)


def test_invalid_limit(self):
    """Test validation with invalid limit"""
    pass


class TestBaseAgent(unittest.TestCase):
    def setUp(self):
        # Mock
        self.event_manager = MagicMock(spec=EventManager)
        self.state_events = BaseAgent.StateEvents(MagicMock(), MagicMock(), MagicMock())
        self.control_events = BaseAgent.ControlEvents(
            MagicMock(), MagicMock(), MagicMock()
        )

        # Create test config
        self.config = BaseAgent.Config()

        # Initialize test agent
        self.agent = MyBaseAgent(
            name="test_base_agent",
            config=self.config,
            a_type="process",
            state_events=self.state_events,
            control_events=self.control_events,
            custom_attr="custom_value",
            event_manager=self.event_manager,
        )

    def test_initialization(self):
        """Test agent initialization"""

        # Check agent attributes
        self.assertEqual(self.agent.name, "test_base_agent")
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

    def test_initialization_with_default_name(self):
        """Test agent initialization with default name"""
        agent = MyBaseAgent(
            name=None,
            config=self.config,
            a_type="process",
            state_events=self.state_events,
            control_events=self.control_events,
            event_manager=self.event_manager,
        )
        self.assertEqual(agent.name, "MyBaseAgent")

    def test_initialization_with_custom_config(self):
        """Test agent initialization with custom configuration"""
        custom_config = BaseAgent.Config(
            logger_config=LoggerConfig(level="WARNING", filename="test.log")
        )

        agent = MyBaseAgent(
            name="test_agent",
            config=custom_config,
            a_type="process",
            state_events=self.state_events,
            control_events=self.control_events,
            event_manager=self.event_manager,
        )
        self.assertEqual(agent.config.logger_config.level, "WARNING")
        self.assertEqual(agent.config.logger_config.filename, "test.log")

    def test_stop(self):
        """Test stop method"""
        self.agent.logger = MagicMock()
        self.agent.on_stop = MagicMock()
        self.agent.stop()
        self.control_events.stop_event.set.assert_called_once()
        self.agent.on_stop.assert_called_once()

    def test_validate_config_success(self):
        """Test successful config validation"""
        self.agent.logger = MagicMock()
        self.config.validate = MagicMock()
        self.agent.validate_config()
        self.config.validate.assert_called_once()

    def test_validate_config_failure(self):
        """Test failed config validation"""
        self.agent.logger = MagicMock()
        self.config.validate = MagicMock(side_effect=Exception("Invalid config"))
        with self.assertRaises(ValidationError):
            self.agent.validate_config()

    def test_setup(self):
        """Test setup method"""
        self.agent.logger = MagicMock()
        self.agent.setup()
        self.control_events.setup_event.wait.assert_called_once()

    def test_execute(self):
        """Test execute method"""
        self.agent.logger = MagicMock()
        self.agent.execute()
        self.control_events.execute_event.wait.assert_called_once()

    def test_run_lifecycle(self):
        """Test complete run lifecycle"""
        self.agent.setup = MagicMock()
        self.agent.execute = MagicMock()
        self.agent.validate_config = MagicMock()  # type:ignore

        self.agent.run()

        self.agent.setup.assert_called_once()
        self.agent.execute.assert_called_once()
        self.agent.validate_config.assert_called_once()
        self.state_events.ready_event.set.assert_called_once()
        self.state_events.close_event.set.assert_called_once()

    def test_run_with_exception(self):
        """Test run method with exception"""
        self.agent.execute = MagicMock(side_effect=Exception("Test error"))
        self.agent.run()
        self.state_events.close_event.set.assert_called_once()

    def test_on_stop_is_called(self):
        """Test on_stop method is called during stop."""
        self.agent.logger = MagicMock()
        self.agent.on_stop = MagicMock()
        self.agent.stop()
        self.agent.on_stop.assert_called_once()

    def test_on_close_is_called(self):
        """Test on_close method is called during run."""
        self.agent.logger = MagicMock()
        self.agent.on_close = MagicMock()
        self.agent.run()
        self.agent.on_close.assert_called_once()

    @patch.object(BaseAgent, "_info")
    def test_info_is_called_during_run(self, mock_info):
        """Test _info method is called during run."""
        self.agent.logger = MagicMock()
        self.agent.run()
        mock_info.assert_called_once()

    def test_run_with_missing_events(self):
        """Test run method with missing events."""
        agent_missing = MyBaseAgent(
            name="test_agent_missing_events",
            config=self.config,
            a_type="process",
            control_events=None,  # type:ignore
            state_events=None,  # type:ignore
            event_manager=self.event_manager,
        )
        agent_missing.logger = MagicMock()

        agent_missing.run()

        agent_missing.logger.exception.assert_not_called()

    def test_run_with_exception_in_setup(self):
        """Test run method con eccezione in setup."""
        self.agent.setup = MagicMock(side_effect=Exception("Test setup error"))

        self.agent.run()
        self.state_events.close_event.set.assert_called_once()

    def test_event_manager_emit_calls(self):
        """Test event manager emit calls during run."""
        self.agent.logger = MagicMock()
        self.agent.run()
        self.event_manager.emit.assert_any_call(AgentEvent.AGENT_START)
        self.event_manager.emit.assert_any_call(AgentEvent.AGENT_READY)
        self.event_manager.emit.assert_any_call(AgentEvent.AGENT_CLOSE)


if __name__ == "__main__":
    unittest.main()
