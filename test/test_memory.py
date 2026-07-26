import unittest
from PyOrchestrate.core.orchestrator.memory import OMemory
from PyOrchestrate.core.agent.base_agent import BaseThreadAgent


class DummyAgent(BaseThreadAgent):
    def execute(self):
        super().execute()


class TestOMemoryEventLogging(unittest.TestCase):
    def test_event_logging(self):
        memory = OMemory()
        entry = memory.add_agent(DummyAgent, "agent1")
        entry._initialize_instance()
        entry._start_instance()
        entry._join_instance()
        events = memory.get_agent_stats("agent1")
        self.assertEqual(len(events), 2)
        self.assertEqual([e["event"] for e in events], ["start", "join"])


if __name__ == "__main__":
    unittest.main()
