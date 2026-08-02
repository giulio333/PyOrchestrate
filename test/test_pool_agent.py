"""
Tests for PoolAgent.

They cover the inner orchestrator built by ``PoolAgent.setup()``: how it is
configured, and how the entries of ``agents_entry`` are registered on it.
"""

import threading
import unittest

from PyOrchestrate.core.agent.looping_agent import LoopingThreadAgent
from PyOrchestrate.core.agent.pool_agent import PoolThreadAgent
from PyOrchestrate.core.orchestrator.memory import AgentEntry
from PyOrchestrate.core.orchestrator.orchestrator import OrchestratorConfig
from PyOrchestrate.core.utilities.validation import ValidationSeverity


class ChildAgent(LoopingThreadAgent):
    """Thread agent that performs a single cycle and terminates."""

    class Config(LoopingThreadAgent.Config):
        limit = 1

    config: Config

    def cycle(self):
        pass


def make_control_events() -> ChildAgent.ControlEvents:
    """Control events already released, so the child runs without a supervisor."""
    setup_event, execute_event = threading.Event(), threading.Event()
    setup_event.set()
    execute_event.set()
    return ChildAgent.ControlEvents(setup_event, execute_event, threading.Event())


def make_state_events() -> ChildAgent.StateEvents:
    return ChildAgent.StateEvents(
        threading.Event(), threading.Event(), threading.Event()
    )


class TestPoolAgentConfig(unittest.TestCase):

    def test_orchestrator_config_defaults_to_none(self):
        config = PoolThreadAgent.Config()
        self.assertIsNone(config.orchestrator_config)

    def test_orchestrator_config_is_stored(self):
        inner_config = OrchestratorConfig(max_workers=3)
        config = PoolThreadAgent.Config(orchestrator_config=inner_config)
        self.assertIs(config.orchestrator_config, inner_config)

    def test_invalid_orchestrator_config_is_reported(self):
        config = PoolThreadAgent.Config(
            agents_entry=[AgentEntry(ChildAgent, "child")],
            orchestrator_config="tcp://*:5556",  # type: ignore[arg-type]
        )

        results = config.validate()
        errors = [
            result
            for result in results
            if result.field == "orchestrator_config"
            and result.severity == ValidationSeverity.ERROR
        ]
        self.assertEqual(len(errors), 1)

    def test_valid_orchestrator_config_is_not_reported(self):
        config = PoolThreadAgent.Config(
            agents_entry=[AgentEntry(ChildAgent, "child")],
            orchestrator_config=OrchestratorConfig(enable_command_interface=False),
        )

        results = config.validate()
        self.assertEqual(
            [result for result in results if result.field == "orchestrator_config"], []
        )


class TestPoolAgentSetup(unittest.TestCase):
    """Exercises the real inner orchestrator, no mocks."""

    def setUp(self):
        self.pools: list[PoolThreadAgent] = []

    def tearDown(self):
        for pool in self.pools:
            orchestrator = pool._orchestrator
            if orchestrator is None:
                continue
            orchestrator.stop()
            if orchestrator.memory.agents:
                orchestrator.join()
            else:
                # Without agents setup() returns before start(), and join()
                # would trip over the start_time that start() sets.
                orchestrator._shutdown_channel_handlers()

    def make_pool(self, name: str, **config_kwargs) -> PoolThreadAgent:
        pool = PoolThreadAgent(
            name=name, config=PoolThreadAgent.Config(**config_kwargs)
        )
        # Out of a running agent, nothing has called setup_logger() yet.
        pool.setup_logger()
        self.pools.append(pool)
        return pool

    def test_inner_orchestrator_has_no_command_interface_by_default(self):
        """The default command port belongs to the parent orchestrator."""
        pool = self.make_pool("pool")
        pool.setup()

        self.assertFalse(pool.orchestrator.config.enable_command_interface)
        self.assertIsNone(pool.orchestrator.command_interface)

    def test_inner_orchestrator_uses_the_configured_config(self):
        inner_config = OrchestratorConfig(
            max_workers=3, enable_command_interface=False, check_interval=0.5
        )
        pool = self.make_pool("pool", orchestrator_config=inner_config)
        pool.setup()

        self.assertIs(pool.orchestrator.config, inner_config)
        self.assertEqual(pool.orchestrator.config.max_workers, 3)

    def test_several_pools_can_be_set_up_side_by_side(self):
        """Two pools used to fight over tcp://*:5555 and die on startup."""
        for index in range(2):
            pool = self.make_pool(
                f"pool{index}",
                agents_entry=[
                    AgentEntry(
                        ChildAgent,
                        f"child{index}",
                        control_events=make_control_events(),
                        state_events=make_state_events(),
                    )
                ],
            )
            pool.setup()

            self.assertIsNone(pool.orchestrator.command_interface)
            self.assertEqual(len(pool.orchestrator.memory.agents), 1)

    def test_entry_fields_reach_their_own_register_agent_parameters(self):
        """Passed positionally, plugin and events landed on the wrong parameters."""
        config = ChildAgent.Config(limit=1)
        plugin = ChildAgent.Plugin()
        control_events = make_control_events()
        state_events = make_state_events()

        pool = self.make_pool(
            "pool",
            agents_entry=[
                AgentEntry(
                    ChildAgent,
                    "child",
                    config=config,
                    plugin=plugin,
                    control_events=control_events,
                    state_events=state_events,
                    custom_kwarg="custom_value",
                )
            ],
        )
        pool.setup()

        registered = pool.orchestrator.memory.agents[0]
        self.assertIs(registered.config, config)
        self.assertIs(registered.plugin, plugin)
        self.assertIs(registered.control_events, control_events)
        self.assertIs(registered.state_events, state_events)
        self.assertEqual(registered.kwargs["custom_kwarg"], "custom_value")

    def test_pool_without_agents_registers_nothing(self):
        pool = self.make_pool("pool")
        pool.setup()

        self.assertEqual(pool.orchestrator.memory.agents, [])


if __name__ == "__main__":
    unittest.main()
