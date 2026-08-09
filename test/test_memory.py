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


class TestUninitializedEntry(unittest.TestCase):
    """An entry only has an instance once a startup attempt built one."""

    def test_instance_raises_a_real_exception(self):
        """The guard was an assert, which python -O strips."""
        memory = OMemory()
        entry = memory.add_agent(DummyAgent, "registered")

        with self.assertRaises(RuntimeError):
            entry.instance

    def test_group_agents_skips_members_without_an_instance(self):
        """Reading the group used to raise for any member not yet started."""
        memory = OMemory()
        started = memory.add_agent(DummyAgent, "started")
        memory.add_agent(DummyAgent, "registered")
        memory.create_group("group")
        memory.add_agent_to_group("started", "group")
        memory.add_agent_to_group("registered", "group")
        started._initialize_instance()

        instances = memory.get_group_agents("group")

        self.assertEqual([instance.name for instance in instances], ["started"])


if __name__ == "__main__":
    unittest.main()
