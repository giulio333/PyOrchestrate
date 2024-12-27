import unittest
from unittest.mock import MagicMock, patch
import sys, os

from PyOrchestrate.core.base.base import BaseAgent, BaseThreadAgent, BaseConfig, BaseProcessAgent


class TestAbstractBaseAgent(unittest.TestCase):
    def setUp(self):
        # Creazione di una sottoclasse per testare AbstractBaseAgent
        class TestAgent(BaseAgent):
            def stop(self):
                pass

            def execute(self):
                pass

        self.agent_class = TestAgent
        self.agent = self.agent_class(name="TestAgent")

    def test_initialization(self):
        # Verifica che l'agent venga inizializzato correttamente
        self.assertEqual(self.agent.name, "TestAgent")
        self.assertIsNone(self.agent.logger)
        self.assertIsInstance(self.agent.config, BaseConfig)

    @patch("PyOrchestrate.core.base.baseagent.LoggerFactory.create_logger")
    def test_setup_logger(self, mock_create_logger):
        # Simula il seup del logger
        mock_logger = MagicMock()
        mock_create_logger.return_value = mock_logger

        self.agent.setup_logger()
        self.assertIsNotNone(self.agent.logger)
        mock_create_logger.assert_called_once()

    @patch("PyOrchestrate.core.base.baseagent.LoggerFactory.create_logger")
    def test_validate_config(self, mock_create_logger):
        # Testa il metodo validate_config
        mock_logger = MagicMock()
        mock_create_logger.return_value = mock_logger

        self.agent.setup_logger()
        self.agent.validate_config()

        mock_logger.info.assert_any_call("Configuration successfully validated.")

    @patch("PyOrchestrate.core.base.baseagent.LoggerFactory.create_logger")
    @patch("time.time", return_value=100.0)
    def test_run_agent(self, mock_time, mock_create_logger):
        # Testa il ciclo principale di un agent
        mock_logger = MagicMock()
        mock_create_logger.return_value = mock_logger

        with patch.object(self.agent, "execute") as mock_execute:
            self.agent.run_agent()
            mock_execute.assert_called_once()

        mock_logger.info.assert_any_call("Starting agent...")


class TestBaseThreadAgent(unittest.TestCase):
    def setUp(self):
        self.thread_agent = BaseThreadAgent(name="TestThreadAgent")

    def test_thread_initialization(self):
        self.assertEqual(self.thread_agent.name, "TestThreadAgent")
        self.assertFalse(self.thread_agent._stop_event.is_set())

    def test_thread_stop(self):
        self.thread_agent.stop()
        self.assertTrue(self.thread_agent._stop_event.is_set())


class TestBaseProcessAgent(unittest.TestCase):
    def setUp(self):
        self.process_agent = BaseProcessAgent(name="TestProcessAgent")

    def test_process_initialization(self):
        self.assertEqual(self.process_agent.name, "TestProcessAgent")
        self.assertFalse(self.process_agent._stop_event.is_set())

    def test_process_stop(self):
        self.process_agent.stop()
        self.assertTrue(self.process_agent._stop_event.is_set())


if __name__ == "__main__":
    unittest.main()
