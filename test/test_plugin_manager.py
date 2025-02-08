import unittest
from unittest.mock import MagicMock, patch
import zmq

from PyOrchestrate.core.plugins.plugin_manager import PluginManager
from PyOrchestrate.core.plugins.communication_plugins import ZeroMQPubSub


class TestPluginManager(unittest.TestCase):
    def setUp(self):
        self.plugin_manager = PluginManager()

    def test_register_and_unregister_zmq_plugin(self):
        zmq_plugin = ZeroMQPubSub("tcp://localhost:5555", zmq.PUB)
        self.plugin_manager.register(zmq_plugin)
        self.assertIsNotNone(self.plugin_manager._cp)

        with patch.object(
            zmq_plugin, "finalize", wraps=zmq_plugin.finalize
        ) as mock_finalize:
            self.plugin_manager.unregister()
            mock_finalize.assert_called_once()

        self.assertIsNone(self.plugin_manager._cp)

    def test_unregister_without_registering(self):
        with self.assertRaises(AttributeError):
            self.plugin_manager.unregister()

    def test_zmq_context_closed_on_unregister(self):
        zmq_plugin = ZeroMQPubSub("tcp://localhost:5555", zmq.PUB)
        self.plugin_manager.register(zmq_plugin)
        self.assertIsNotNone(self.plugin_manager._cp)

        with patch.object(
            zmq_plugin.context, "term", wraps=zmq_plugin.context.term
        ) as mock_term:
            self.plugin_manager.unregister()
            mock_term.assert_called_once()

        self.assertIsNone(self.plugin_manager._cp)


if __name__ == "__main__":
    unittest.main()
