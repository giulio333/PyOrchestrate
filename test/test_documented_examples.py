"""
Regression tests for the agents shown in the documentation.

Every class here mirrors a snippet a reader can copy off the site. The point is
not to exercise the framework — other modules do that — but to make the docs
fail in CI instead of on the reader's machine: each of these examples used to
raise ``TypeError`` when instantiated or registered.

Issues #87 and #88.
"""

import unittest

import zmq

from PyOrchestrate.core.agent import (
    BaseProcessAgent,
    LoopingProcessAgent,
    PeriodicProcessAgent,
)
from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator
from PyOrchestrate.core.plugins import (
    SocketType,
    ZeroMQPair,
    ZeroMQPubSub,
    ZeroMQSocketPlugin,
)


def _orchestrator() -> Orchestrator:
    """An orchestrator that does not bind the command port."""
    return Orchestrator(config=Orchestrator.Config(enable_command_interface=False))


class TestLoopingAgentExample(unittest.TestCase):
    """docs/learn/agents/built-in-agents/loopingagent.mdx"""

    def test_log_monitor_agent_is_instantiable(self):
        """
        The documented LogMonitorAgent must implement ``cycle``.

        It used to override ``execute``, which is ``@final`` on LoopingAgent,
        leaving the ``cycle`` abstract method unimplemented.
        """

        class LogMonitorAgent(LoopingProcessAgent):
            class Config(LoopingProcessAgent.Config):
                log_file: str = "app.log"
                keyword: str = "ERROR"

            config: Config

            def cycle(self):
                super().cycle()

        agent = LogMonitorAgent(name="log_monitor")

        self.assertEqual(agent.name, "log_monitor")
        self.assertEqual(agent.config.keyword, "ERROR")

    def test_overriding_execute_alone_is_not_enough(self):
        """
        Overriding ``execute`` does not satisfy the abstract ``cycle``.

        This is the exact failure the documented example produced.
        """

        class BrokenAgent(LoopingProcessAgent):
            def execute(self):
                super().execute()

        with self.assertRaises(TypeError) as ctx:
            BrokenAgent(name="broken")

        self.assertIn("cycle", str(ctx.exception))


class TestPeriodicAgentExample(unittest.TestCase):
    """docs/examples/basic/project-initialization.mdx"""

    def test_weather_collector_uses_its_own_config(self):
        """
        ``Config = WCConfig`` is what binds a config class to an agent.

        The page used to write ``config = WCConfig`` (lowercase), which
        ``__init__`` overwrites, so the custom config was silently ignored.
        """

        class WCConfig(PeriodicProcessAgent.Config):
            limit: int = 2
            execution_interval: float = 2
            url: str = "https://catfact.ninja/fact"

        class WeatherCollector(PeriodicProcessAgent):
            Config = WCConfig

            config: Config

            def runner(self):
                super().runner()

        agent = WeatherCollector(name="weather_collector")

        self.assertIsInstance(agent.config, WCConfig)
        self.assertEqual(agent.config.url, "https://catfact.ninja/fact")
        self.assertEqual(agent.config.limit, 2)

    def test_lowercase_config_does_not_bind_the_class(self):
        """The pattern the page used to show leaves the base config in place."""

        class WCConfig(PeriodicProcessAgent.Config):
            url: str = "https://catfact.ninja/fact"

        class WeatherCollector(PeriodicProcessAgent):
            config = WCConfig

            def runner(self):
                super().runner()

        agent = WeatherCollector(name="weather_collector")

        self.assertNotIsInstance(agent.config, WCConfig)
        self.assertFalse(hasattr(agent.config, "url"))

    def test_agent_classes_are_not_subscriptable(self):
        """
        The agent classes are not generic.

        ``PeriodicProcessAgent[WCConfig]`` raised ``TypeError`` at class
        definition time, which is why the annotation was removed from the page.
        """
        for agent_class in (
            PeriodicProcessAgent,
            LoopingProcessAgent,
            BaseProcessAgent,
        ):
            with self.subTest(agent_class=agent_class.__name__):
                with self.assertRaises(TypeError):
                    agent_class[PeriodicProcessAgent.Config]


class TestCommunicationPluginExample(unittest.TestCase):
    """docs/learn/agents/plugins/communication-plugins.mdx"""

    def test_manual_agent_can_be_registered(self):
        """
        An agent that declares ``__init__`` must forward ``**kwargs``.

        ``register_agent`` constructs agents with ``name``, ``config``,
        ``plugin``, ``control_events``, ``state_events`` and ``generation_id``;
        the documented ``def __init__(self)`` rejected every one of them.
        """

        class MyAgent(BaseProcessAgent):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.initialized = True

            def execute(self):
                super().execute()

        entry = _orchestrator().register_agent(MyAgent, "my_agent")
        entry._initialize_instance()

        self.assertIsInstance(entry.instance, MyAgent)
        self.assertTrue(entry.instance.initialized)
        self.assertEqual(entry.instance.name, "my_agent")

    def test_init_without_kwargs_cannot_be_registered(self):
        """The signature the page used to show, and the error it produced."""

        class MyAgent(BaseProcessAgent):
            def __init__(self):
                super().__init__()

            def execute(self):
                super().execute()

        entry = _orchestrator().register_agent(MyAgent, "my_agent")

        with self.assertRaises(TypeError):
            entry._initialize_instance()


class TestCustomSocketPluginExample(unittest.TestCase):
    """docs/learn/agents/plugins/communication-plugins.mdx"""

    def test_subclassing_zeromqsocketplugin_needs_only_initialize(self):
        """
        The page tells the reader that ``initialize()`` is the only method a
        custom socket plugin has to write. This is that snippet, verbatim.
        """

        class ZeroMQXPubXSub(ZeroMQSocketPlugin):

            def initialize(self):
                if self._initialized:
                    return

                self._socket = self.context.socket(zmq.XPUB)
                self._socket.bind(self.address)

                self._initialized = True

        plugin = ZeroMQXPubXSub("tcp://127.0.0.1:5701")
        plugin.initialize()

        # Inherited, and never declared by the subclass.
        self.assertIsNotNone(plugin.socket)
        plugin.setsockopt(zmq.LINGER, 0)
        self.assertIsNone(plugin.set_owner(object()))

        plugin.finalize()
        self.assertFalse(plugin._initialized)

    def test_shared_context_teardown_order(self):
        """
        The page hands one context to two plugins and terminates it last. If a
        plugin terminated a context it was given, this sequence would block on
        the sibling's open socket instead of finishing.
        """
        context = zmq.Context()

        inbox = ZeroMQPair("tcp://127.0.0.1:5711", context=context)
        events = ZeroMQPubSub("tcp://127.0.0.1:5712", SocketType.PUB, context=context)

        inbox.initialize()
        events.initialize()

        inbox.finalize()
        self.assertFalse(context.closed)

        events.finalize()
        context.term()

        self.assertTrue(context.closed)


if __name__ == "__main__":
    unittest.main()
