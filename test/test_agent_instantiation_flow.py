"""
Test agent instantiation flow verification.

This test validates that the agent instantiation process is coherent
and that all variables (config, plugin, control_events, state_events, msg_channel)
are correctly passed through all layers:

1. Orchestrator.register_agent()
2. OMemory.add_agent()
3. AgentEntry creation
4. AgentEntry.initialize_agent()
5. Agent __init__()
6. Agent.run() and lifecycle
"""

import unittest
import multiprocessing
import threading
from unittest.mock import patch

from PyOrchestrate.core.agent.base_agent import (
    BaseAgent,
    BaseProcessAgent,
    BaseThreadAgent,
)
from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator
from PyOrchestrate.core.orchestrator.memory import OMemory, AgentEntry
from PyOrchestrate.core.utilities.messaging import MessageChannel


class TestAgentInstantiationFlow(unittest.TestCase):
    """
    Test suite to verify the complete agent instantiation flow.

    This test verifies that:
    1. Config is correctly passed from registration to agent instance
    2. Plugin is correctly passed from registration to agent instance
    3. Events (control_events, state_events) are correctly created and passed
    4. MessageChannel is correctly passed or created
    5. Additional kwargs are correctly passed
    """

    def setUp(self):
        """Set up test fixtures."""
        # Create a simple test agent
        class SimpleTestAgent(BaseProcessAgent):
            class Config(BaseProcessAgent.Config):
                test_value: str = "default"
                number: int = 42

            config: Config

            def execute(self):
                super().execute()
                # Simple execution - just for testing
                pass

        self.SimpleTestAgent = SimpleTestAgent

    def test_config_propagation_through_registration(self):
        """
        Test that custom config is correctly propagated through the registration process.

        Flow: Orchestrator.register_agent() → AgentEntry → Agent instance
        """
        # Create custom config
        custom_config = self.SimpleTestAgent.Config(
            test_value="custom_value",
            number=100
        )

        # Create orchestrator (disable command interface to avoid port conflicts in tests)
        orchestrator = Orchestrator(
            config=Orchestrator.Config(enable_command_interface=False)
        )

        # Register agent with custom config
        agent_entry = orchestrator.register_agent(
            self.SimpleTestAgent,
            "test_agent",
            custom_config=custom_config
        )

        # Verify config is stored in AgentEntry
        self.assertIsNotNone(agent_entry.config)
        self.assertEqual(agent_entry.config.test_value, "custom_value")
        self.assertEqual(agent_entry.config.number, 100)

        # Initialize agent (this creates the actual agent instance)
        agent_entry.initialize_agent()

        # Verify config is passed to agent instance
        self.assertIsNotNone(agent_entry.instance.config)
        self.assertEqual(agent_entry.instance.config.test_value, "custom_value")
        self.assertEqual(agent_entry.instance.config.number, 100)

        # Verify it's the same config object
        self.assertIs(agent_entry.instance.config, custom_config)

    def test_default_config_when_none_provided(self):
        """
        Test that default config is used when no custom config is provided.
        """
        orchestrator = Orchestrator(
            config=Orchestrator.Config(enable_command_interface=False)
        )

        # Register agent WITHOUT custom config
        agent_entry = orchestrator.register_agent(
            self.SimpleTestAgent,
            "test_agent"
        )

        # Config should be None in AgentEntry until initialization
        self.assertIsNone(agent_entry.config)

        # Initialize agent
        agent_entry.initialize_agent()

        # Now agent should have default config
        self.assertIsNotNone(agent_entry.instance.config)
        self.assertEqual(agent_entry.instance.config.test_value, "default")
        self.assertEqual(agent_entry.instance.config.number, 42)

    def test_plugin_propagation_through_registration(self):
        """
        Test that custom plugin is correctly propagated through the registration process.
        """
        # Create custom plugin
        custom_plugin = self.SimpleTestAgent.Plugin()

        orchestrator = Orchestrator(
            config=Orchestrator.Config(enable_command_interface=False)
        )

        # Register agent with custom plugin
        agent_entry = orchestrator.register_agent(
            self.SimpleTestAgent,
            "test_agent",
            custom_plugin=custom_plugin
        )

        # Verify plugin is stored in AgentEntry
        self.assertIsNotNone(agent_entry.plugin)

        # Initialize agent
        agent_entry.initialize_agent()

        # Verify plugin is passed to agent instance
        self.assertIsNotNone(agent_entry.instance.plugin)

        # Verify it's the same plugin object
        self.assertIs(agent_entry.instance.plugin, custom_plugin)

    def test_control_events_propagation(self):
        """
        Test that control_events are correctly created or passed through registration.
        """
        orchestrator = Orchestrator(
            config=Orchestrator.Config(enable_command_interface=False)
        )

        # Case 1: No custom control events (will be None until agent initialization)
        agent_entry1 = orchestrator.register_agent(
            self.SimpleTestAgent,
            "test_agent1"
        )

        # Control events are None in AgentEntry until initialization
        self.assertIsNone(agent_entry1.control_events)

        # Initialize agent
        agent_entry1.initialize_agent()

        # After initialization, agent creates its own control events
        self.assertIsNotNone(agent_entry1.instance.control_events)
        self.assertIsNotNone(agent_entry1.instance.control_events.setup_event)
        self.assertIsNotNone(agent_entry1.instance.control_events.execute_event)
        self.assertIsNotNone(agent_entry1.instance.control_events.stop_event)

        # Case 2: Custom control events
        custom_control_events = BaseAgent.ControlEvents(
            setup_event=multiprocessing.Event(),
            execute_event=multiprocessing.Event(),
            stop_event=multiprocessing.Event()
        )

        agent_entry2 = orchestrator.register_agent(
            self.SimpleTestAgent,
            "test_agent2",
            control_events=custom_control_events
        )

        # Verify custom control events are stored
        self.assertIs(agent_entry2.control_events, custom_control_events)

        agent_entry2.initialize_agent()

        # Verify custom control events are passed to agent
        self.assertIs(agent_entry2.instance.control_events, custom_control_events)

    def test_state_events_propagation(self):
        """
        Test that state_events are correctly created or passed through registration.
        """
        orchestrator = Orchestrator(
            config=Orchestrator.Config(enable_command_interface=False)
        )

        # Case 1: No custom state events (will be None until agent initialization)
        agent_entry1 = orchestrator.register_agent(
            self.SimpleTestAgent,
            "test_agent1"
        )

        # State events are None in AgentEntry until initialization
        self.assertIsNone(agent_entry1.state_events)

        # Initialize agent
        agent_entry1.initialize_agent()

        # After initialization, agent creates its own state events
        self.assertIsNotNone(agent_entry1.instance.state_events)
        self.assertIsNotNone(agent_entry1.instance.state_events.start_event)
        self.assertIsNotNone(agent_entry1.instance.state_events.ready_event)
        self.assertIsNotNone(agent_entry1.instance.state_events.close_event)

        # Case 2: Custom state events
        custom_state_events = BaseAgent.StateEvents(
            start_event=multiprocessing.Event(),
            ready_event=multiprocessing.Event(),
            close_event=multiprocessing.Event()
        )

        agent_entry2 = orchestrator.register_agent(
            self.SimpleTestAgent,
            "test_agent2",
            state_events=custom_state_events
        )

        # Verify custom state events are stored
        self.assertIs(agent_entry2.state_events, custom_state_events)

        agent_entry2.initialize_agent()

        # Verify custom state events are passed to agent
        self.assertIs(agent_entry2.instance.state_events, custom_state_events)

    def test_message_channel_propagation(self):
        """
        Test that msg_channel is correctly passed or created.
        """
        orchestrator = Orchestrator(
            config=Orchestrator.Config(enable_command_interface=False)
        )

        # Case 1: No custom msg_channel (orchestrator's channel should be used)
        agent_entry1 = orchestrator.register_agent(
            self.SimpleTestAgent,
            "test_agent1"
        )

        agent_entry1.initialize_agent()

        # Verify msg_channel exists
        self.assertIsNotNone(agent_entry1.instance.msg_channel)

        # Should be the orchestrator's msg_channel
        self.assertIs(agent_entry1.instance.msg_channel, orchestrator.msg_channel)

        # Case 2: Custom msg_channel
        custom_msg_channel = MessageChannel("process")

        agent_entry2 = orchestrator.register_agent(
            self.SimpleTestAgent,
            "test_agent2",
            msg_channel=custom_msg_channel
        )

        agent_entry2.initialize_agent()

        # Verify custom msg_channel is used
        self.assertIs(agent_entry2.instance.msg_channel, custom_msg_channel)

    def test_additional_kwargs_propagation(self):
        """
        Test that additional kwargs are correctly passed to the agent.
        """
        orchestrator = Orchestrator(
            config=Orchestrator.Config(enable_command_interface=False)
        )

        # Register agent with additional kwargs
        agent_entry = orchestrator.register_agent(
            self.SimpleTestAgent,
            "test_agent",
            custom_attr="custom_value",
            another_attr=123
        )

        # Verify kwargs are stored in AgentEntry
        self.assertIn("custom_attr", agent_entry.kwargs)
        self.assertEqual(agent_entry.kwargs["custom_attr"], "custom_value")
        self.assertIn("another_attr", agent_entry.kwargs)
        self.assertEqual(agent_entry.kwargs["another_attr"], 123)

        # Initialize agent
        agent_entry.initialize_agent()

        # Verify kwargs are passed to agent instance
        self.assertTrue(hasattr(agent_entry.instance, "custom_attr"))
        self.assertEqual(agent_entry.instance.custom_attr, "custom_value")
        self.assertTrue(hasattr(agent_entry.instance, "another_attr"))
        self.assertEqual(agent_entry.instance.another_attr, 123)

    def test_agent_name_propagation(self):
        """
        Test that agent name is correctly passed through all layers.
        """
        orchestrator = Orchestrator(
            config=Orchestrator.Config(enable_command_interface=False)
        )

        agent_name = "MySpecialAgent"

        agent_entry = orchestrator.register_agent(
            self.SimpleTestAgent,
            agent_name
        )

        # Verify name in AgentEntry
        self.assertEqual(agent_entry.name, agent_name)

        # Initialize agent
        agent_entry.initialize_agent()

        # Verify name in agent instance
        self.assertEqual(agent_entry.instance.name, agent_name)

    def test_agent_type_for_process_agent(self):
        """
        Test that agent type is correctly set for ProcessAgent.
        """
        orchestrator = Orchestrator(
            config=Orchestrator.Config(enable_command_interface=False)
        )

        agent_entry = orchestrator.register_agent(
            self.SimpleTestAgent,
            "test_agent"
        )

        agent_entry.initialize_agent()

        # Verify agent type
        self.assertEqual(agent_entry.instance.a_type, "process")

        # Verify it's a multiprocessing.Process
        self.assertIsInstance(agent_entry.instance, multiprocessing.Process)

    def test_agent_type_for_thread_agent(self):
        """
        Test that agent type is correctly set for ThreadAgent.
        """
        class SimpleThreadAgent(BaseThreadAgent):
            def execute(self):
                super().execute()

        orchestrator = Orchestrator(
            config=Orchestrator.Config(enable_command_interface=False)
        )

        agent_entry = orchestrator.register_agent(
            SimpleThreadAgent,
            "test_agent"
        )

        agent_entry.initialize_agent()

        # Verify agent type
        self.assertEqual(agent_entry.instance.a_type, "thread")

        # Verify it's a threading.Thread
        self.assertIsInstance(agent_entry.instance, threading.Thread)

    def test_complete_instantiation_flow_integration(self):
        """
        Integration test: verify complete instantiation flow from orchestrator to agent.

        This test validates the entire flow:
        1. Orchestrator.register_agent() with custom config and plugin
        2. AgentEntry stores all parameters correctly
        3. AgentEntry.initialize_agent() creates agent with all parameters
        4. Agent receives all parameters correctly
        """
        # Create custom config and plugin
        custom_config = self.SimpleTestAgent.Config(
            test_value="integration_test",
            number=999
        )
        custom_plugin = self.SimpleTestAgent.Plugin()

        # Create custom events
        custom_control_events = BaseAgent.ControlEvents(
            setup_event=multiprocessing.Event(),
            execute_event=multiprocessing.Event(),
            stop_event=multiprocessing.Event()
        )
        custom_state_events = BaseAgent.StateEvents(
            start_event=multiprocessing.Event(),
            ready_event=multiprocessing.Event(),
            close_event=multiprocessing.Event()
        )

        # Create custom msg_channel
        custom_msg_channel = MessageChannel("process")

        # Create orchestrator
        orchestrator = Orchestrator(
            config=Orchestrator.Config(enable_command_interface=False)
        )

        # Register agent with all custom parameters
        agent_entry = orchestrator.register_agent(
            self.SimpleTestAgent,
            "integration_test_agent",
            custom_config=custom_config,
            custom_plugin=custom_plugin,
            control_events=custom_control_events,
            state_events=custom_state_events,
            msg_channel=custom_msg_channel,
            extra_param="extra_value"
        )

        # Verify AgentEntry stores all parameters
        self.assertEqual(agent_entry.name, "integration_test_agent")
        self.assertIs(agent_entry.config, custom_config)
        self.assertIs(agent_entry.plugin, custom_plugin)
        self.assertIs(agent_entry.control_events, custom_control_events)
        self.assertIs(agent_entry.state_events, custom_state_events)
        self.assertEqual(agent_entry.kwargs["msg_channel"], custom_msg_channel)
        self.assertEqual(agent_entry.kwargs["extra_param"], "extra_value")

        # Initialize agent
        agent_entry.initialize_agent()

        # Verify all parameters are passed to agent instance
        self.assertEqual(agent_entry.instance.name, "integration_test_agent")
        self.assertIs(agent_entry.instance.config, custom_config)
        self.assertIs(agent_entry.instance.plugin, custom_plugin)
        self.assertIs(agent_entry.instance.control_events, custom_control_events)
        self.assertIs(agent_entry.instance.state_events, custom_state_events)
        self.assertIs(agent_entry.instance.msg_channel, custom_msg_channel)
        self.assertEqual(agent_entry.instance.extra_param, "extra_value")

        # Verify config values are accessible
        self.assertEqual(agent_entry.instance.config.test_value, "integration_test")
        self.assertEqual(agent_entry.instance.config.number, 999)


class TestOMemoryAgentEntry(unittest.TestCase):
    """
    Test suite specifically for OMemory and AgentEntry initialization.
    """

    def setUp(self):
        """Set up test fixtures."""
        class SimpleAgent(BaseProcessAgent):
            def execute(self):
                super().execute()

        self.SimpleAgent = SimpleAgent
        self.memory = OMemory()

    def test_agent_entry_creation_in_memory(self):
        """
        Test that AgentEntry is correctly created in OMemory.
        """
        custom_config = self.SimpleAgent.Config()

        agent_entry = self.memory.add_agent(
            agent_class=self.SimpleAgent,
            name="test_agent",
            custom_config=custom_config
        )

        # Verify AgentEntry is created correctly
        self.assertIsInstance(agent_entry, AgentEntry)
        self.assertEqual(agent_entry.name, "test_agent")
        self.assertEqual(agent_entry.agent_class, self.SimpleAgent)
        self.assertIs(agent_entry.config, custom_config)

    def test_agent_entry_initialize_creates_instance(self):
        """
        Test that AgentEntry.initialize_agent() creates the agent instance.
        """
        agent_entry = self.memory.add_agent(
            agent_class=self.SimpleAgent,
            name="test_agent"
        )

        # Before initialization, instance should be None
        self.assertIsNone(agent_entry._instance)

        # Initialize
        agent_entry.initialize_agent()

        # After initialization, instance should exist
        self.assertIsNotNone(agent_entry._instance)
        self.assertIsInstance(agent_entry.instance, self.SimpleAgent)

    def test_duplicate_agent_name_raises_error(self):
        """
        Test that adding an agent with duplicate name raises ValueError.
        """
        self.memory.add_agent(
            agent_class=self.SimpleAgent,
            name="duplicate_agent"
        )

        # Try to add another agent with the same name
        with self.assertRaises(ValueError) as context:
            self.memory.add_agent(
                agent_class=self.SimpleAgent,
                name="duplicate_agent"
            )

        self.assertIn("already exists", str(context.exception))


class TestAgentInitializationParameters(unittest.TestCase):
    """
    Test suite to verify that agent __init__ receives correct parameters.
    """

    def test_agent_init_parameters_dict(self):
        """
        Test that AgentEntry.initialize_agent() builds correct parameters dict.
        """
        class TestAgent(BaseProcessAgent):
            def execute(self):
                super().execute()

        custom_config = TestAgent.Config()
        custom_plugin = TestAgent.Plugin()
        custom_control_events = BaseAgent.ControlEvents(
            setup_event=multiprocessing.Event(),
            execute_event=multiprocessing.Event(),
            stop_event=multiprocessing.Event()
        )
        custom_state_events = BaseAgent.StateEvents(
            start_event=multiprocessing.Event(),
            ready_event=multiprocessing.Event(),
            close_event=multiprocessing.Event()
        )

        agent_entry = AgentEntry(
            agent_class=TestAgent,
            name="test_agent",
            config=custom_config,
            plugin=custom_plugin,
            control_events=custom_control_events,
            state_events=custom_state_events,
            extra_kwarg="extra_value"
        )

        # Mock the agent class to inspect the parameters
        with patch.object(TestAgent, '__init__', return_value=None) as mock_init:
            agent_entry.initialize_agent()

            # Verify __init__ was called with correct parameters
            mock_init.assert_called_once()
            call_kwargs = mock_init.call_args[1]

            self.assertEqual(call_kwargs['name'], "test_agent")
            self.assertIs(call_kwargs['config'], custom_config)
            self.assertIs(call_kwargs['plugin'], custom_plugin)
            self.assertIs(call_kwargs['control_events'], custom_control_events)
            self.assertIs(call_kwargs['state_events'], custom_state_events)
            self.assertEqual(call_kwargs['extra_kwarg'], "extra_value")


if __name__ == "__main__":
    unittest.main()
