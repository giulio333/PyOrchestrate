"""
Test cases for the improved plugin instantiation pattern.

These tests verify that the BaseClassPlugin automatically handles
plugin attributes without requiring explicit __init__ implementations.
"""

import unittest
from PyOrchestrate.core.base.base import BaseClassPlugin
from PyOrchestrate.core.agent.base_agent import AgentPlugin
from PyOrchestrate.core.orchestrator.orchestrator import OrchestratorPlugin
from PyOrchestrate.core.plugins.plugin_protocols import PluginProtocol


class MockPlugin(PluginProtocol):
    """Mock plugin for testing."""

    def __init__(self, value: str = "default"):
        self.value = value
        self._initialized = False

    def set_owner(self, owner):
        pass

    def initialize(self):
        self._initialized = True

    def finalize(self):
        self._initialized = False


class TestPluginInstantiation(unittest.TestCase):
    """Test cases for plugin instantiation pattern."""

    def test_base_class_plugin_default_values(self):
        """Test that class attributes serve as defaults."""

        class MyPlugin(BaseClassPlugin):
            mock = MockPlugin("class_default")

        plugin = MyPlugin()
        self.assertEqual(plugin.mock.value, "class_default")

    def test_base_class_plugin_override_via_constructor(self):
        """Test that constructor kwargs override class attributes."""

        class MyPlugin(BaseClassPlugin):
            mock = MockPlugin("class_default")

        override = MockPlugin("constructor_override")
        plugin = MyPlugin(mock=override)
        self.assertEqual(plugin.mock.value, "constructor_override")

    def test_base_class_plugin_multiple_attributes(self):
        """Test handling multiple plugin attributes."""

        class MyPlugin(BaseClassPlugin):
            plugin1 = MockPlugin("plugin1_default")
            plugin2 = MockPlugin("plugin2_default")

        # Use defaults
        plugin_default = MyPlugin()
        self.assertEqual(plugin_default.plugin1.value, "plugin1_default")
        self.assertEqual(plugin_default.plugin2.value, "plugin2_default")

        # Override one
        override1 = MockPlugin("override1")
        plugin_override = MyPlugin(plugin1=override1)
        self.assertEqual(plugin_override.plugin1.value, "override1")
        self.assertEqual(plugin_override.plugin2.value, "plugin2_default")

        # Override both
        override2 = MockPlugin("override2")
        plugin_both = MyPlugin(plugin1=override1, plugin2=override2)
        self.assertEqual(plugin_both.plugin1.value, "override1")
        self.assertEqual(plugin_both.plugin2.value, "override2")

    def test_agent_plugin_simplified_pattern(self):
        """Test that AgentPlugin no longer needs explicit __init__."""

        class MyAgentPlugin(AgentPlugin):
            custom = MockPlugin("custom_default")

        # Verify that MyAgentPlugin inherits __init__ from BaseClassPlugin
        # (no custom __init__ defined in MyAgentPlugin)
        self.assertTrue(MyAgentPlugin.__init__ is BaseClassPlugin.__init__)

        # Test default usage
        plugin1 = MyAgentPlugin()
        self.assertEqual(plugin1.custom.value, "custom_default")

        # Test override
        override = MockPlugin("override")
        plugin2 = MyAgentPlugin(custom=override)
        self.assertEqual(plugin2.custom.value, "override")

    def test_orchestrator_plugin_simplified_pattern(self):
        """Test that OrchestratorPlugin no longer needs explicit __init__."""

        class MyOrchestratorPlugin(OrchestratorPlugin):
            custom = MockPlugin("orchestrator_default")

        # Test default usage
        plugin1 = MyOrchestratorPlugin()
        self.assertEqual(plugin1.custom.value, "orchestrator_default")

        # Test override
        override = MockPlugin("override")
        plugin2 = MyOrchestratorPlugin(custom=override)
        self.assertEqual(plugin2.custom.value, "override")

    def test_none_default_values(self):
        """Test handling None as default value."""

        class MyPlugin(BaseClassPlugin):
            optional_plugin = None

        plugin = MyPlugin()
        self.assertIsNone(plugin.optional_plugin)

        # Override with actual plugin
        override = MockPlugin("provided")
        plugin_with_value = MyPlugin(optional_plugin=override)
        self.assertEqual(plugin_with_value.optional_plugin.value, "provided")

    def test_custom_attr_compatibility(self):
        """Test that _custom_attr mechanism still works."""

        class MyPlugin(BaseClassPlugin):
            default_plugin = MockPlugin("default")

        # Pass arbitrary kwargs
        plugin = MyPlugin(
            default_plugin=MockPlugin("override"),
            extra_param="extra_value",
            another_param=42,
        )

        self.assertEqual(plugin.default_plugin.value, "override")
        self.assertEqual(plugin.extra_param, "extra_value")
        self.assertEqual(plugin.another_param, 42)


if __name__ == "__main__":
    unittest.main()
