import unittest
from unittest.mock import MagicMock, patch

from PyOrchestrate.core.base.pool_agent import PoolAgent, PoolAgentConfig
from PyOrchestrate.core.orchestrator.memory import AgentEntry


class TestPoolAgent(unittest.TestCase):

    def setUp(self):
        self.agent_entry = AgentEntry(agent_class=MagicMock(), name="test_agent")  # type: ignore
        self.config = PoolAgentConfig(
            agents_entry=[self.agent_entry], auto_reboot=True, execution_interval=5.0
        )
        self.pool_agent = PoolAgent(name="test_pool_agent", config=self.config)

    def test_pool_agent_initialization(self):
        self.assertEqual(self.pool_agent.config.auto_reboot, True)
        self.assertEqual(self.pool_agent.config.agents_entry, [self.agent_entry])
        self.assertEqual(self.pool_agent.config.execution_interval, 5.0)

    @patch("core.base.pool_agent.Orchestrator")
    def test_setup(self, MockOrchestrator):
        mock_orchestrator = MockOrchestrator.return_value
        self.pool_agent.setup()
        mock_orchestrator.register_agent.assert_called_once_with(
            self.agent_entry.agent_class, self.agent_entry.name, self.agent_entry.config
        )
        mock_orchestrator.start.assert_called_once()

    @patch("core.base.pool_agent.Orchestrator")
    def test_runner(self, MockOrchestrator):
        mock_orchestrator = MockOrchestrator.return_value
        mock_orchestrator.memory.agents = [
            MagicMock(instance=MagicMock(is_alive=MagicMock(return_value=False)))
        ]
        self.pool_agent.setup()
        self.pool_agent.runner()
        self.assertTrue(self.pool_agent.orchestrator.stop.called)

    def test_orchestrator_property(self):
        with self.assertRaises(RuntimeError):
            _ = self.pool_agent.orchestrator

        self.pool_agent._orchestrator = MagicMock()
        self.assertIsNotNone(self.pool_agent.orchestrator)


if __name__ == "__main__":
    unittest.main()
