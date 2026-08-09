"""Tests for BaseClassConfig.to_dict().

The result reaches the CLI and the web interface as the agent's configuration,
so it has to report everything that actually resolves on the config, in a form
`json.dumps` accepts.
"""

import json
import unittest

from PyOrchestrate.core.agent import PeriodicThreadAgent
from PyOrchestrate.core.base import BaseClassConfig
from PyOrchestrate.core.base.utilities import LoggerConfig
from PyOrchestrate.core.utilities.validation import ValidationPolicy


class DeepConfig(PeriodicThreadAgent.Config):
    """Overrides one inherited default and adds one of its own."""

    execution_interval = 2.0
    retries = 3


class TestConfigToDict(unittest.TestCase):
    """Covers what to_dict() reports and how it renders it."""

    def test_inherited_defaults_are_reported(self):
        """Reading only the leaf class dropped every inherited default."""
        result = DeepConfig().to_dict()

        # limit comes from LoopingAgentConfig, two levels up
        self.assertEqual(result["limit"], -1)
        # delay_compensation comes from PeriodicAgentConfig, one level up
        self.assertEqual(result["delay_compensation"], False)
        # and these come from BaseClassConfig, at the root
        self.assertIn("logger_config", result)
        self.assertIn("validation_policy", result)

    def test_leaf_class_overrides_the_inherited_default(self):
        """A subclass default wins over the one it shadows."""
        self.assertEqual(DeepConfig().to_dict()["execution_interval"], 2.0)
        self.assertEqual(DeepConfig().to_dict()["retries"], 3)

    def test_constructor_arguments_win(self):
        """What the constructor sets is what attribute access returns."""
        config = DeepConfig(execution_interval=0.5, limit=7)

        result = config.to_dict()

        self.assertEqual(result["execution_interval"], 0.5)
        self.assertEqual(result["limit"], 7)

    def test_user_defined_attributes_are_reported(self):
        """_custom_attr holds them, and __getattribute__ resolves them."""
        config = DeepConfig(endpoint="https://example.test", timeout=2.5)

        result = config.to_dict()

        self.assertEqual(result["endpoint"], "https://example.test")
        self.assertEqual(result["timeout"], 2.5)
        self.assertEqual(config.endpoint, result["endpoint"])

    def test_methods_are_not_reported_as_settings(self):
        """validate() lives in the same class dict as the settings."""
        result = DeepConfig().to_dict()

        self.assertNotIn("validate", result)
        self.assertNotIn("to_dict", result)

    def test_result_is_json_serializable(self):
        """The CLI pushes this over ZeroMQ as JSON; one bad value failed it all."""
        config = DeepConfig(
            logger_config=LoggerConfig(level="INFO", filename="agent.log"),
            validation_policy=ValidationPolicy(ignore_errors=True),
        )

        encoded = json.loads(json.dumps(config.to_dict()))

        self.assertEqual(
            encoded["logger_config"], {"level": "INFO", "filename": "agent.log"}
        )
        self.assertEqual(encoded["validation_policy"]["ignore_errors"], True)

    def test_nested_config_is_rendered_through_its_own_to_dict(self):
        """A config holding a config is reported, not stringified."""

        class Inner(BaseClassConfig):
            depth = 1

        class Outer(BaseClassConfig):
            inner = Inner()

        result = Outer().to_dict()

        self.assertEqual(result["inner"]["depth"], 1)

    def test_unencodable_value_falls_back_to_a_string(self):
        """An arbitrary object must not fail the whole response."""

        class Opaque:
            __slots__ = ()

            def __repr__(self):
                return "<opaque>"

        config = BaseClassConfig(handle=Opaque())

        encoded = json.loads(json.dumps(config.to_dict()))

        self.assertEqual(encoded["handle"], "<opaque>")


if __name__ == "__main__":
    unittest.main()
