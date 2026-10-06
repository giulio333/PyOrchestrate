"""Type-checked by `mypy` (listed in `[tool.mypy] files`), never run by pytest.

The annotations are shipped (`py.typed`), so the shape every page of the
documentation teaches -- an inner `Config` re-declared as `config: Config`, an
inner `Plugin` re-declared as `plugin: Plugin` -- has to type-check in a user's
project, including where the framework takes an agent class: `AgentEntry`,
`OMemory.register_agent` and the lifecycle manager all expect
`type[AgentProtocol]`.
"""

from typing import TYPE_CHECKING

from PyOrchestrate.core.agent import (
    AgentProtocol,
    BaseProcessAgent,
    BaseThreadAgent,
    LoopingProcessAgent,
    LoopingThreadAgent,
    PeriodicProcessAgent,
    PeriodicThreadAgent,
    PoolProcessAgent,
    PoolThreadAgent,
)
from PyOrchestrate.core.agent.base_agent import AgentPlugin
from PyOrchestrate.core.orchestrator.memory import AgentEntry


class SensorPlugin(AgentPlugin):
    pass


class Sensor(PeriodicProcessAgent):
    class Config(PeriodicProcessAgent.Config):
        threshold: int = 10

    class Plugin(PeriodicProcessAgent.Plugin):
        pass

    config: Config
    plugin: Plugin

    def runner(self) -> None:
        pass


class ThreadSensor(PeriodicThreadAgent):
    class Config(PeriodicThreadAgent.Config):
        threshold: int = 10

    config: Config

    def runner(self) -> None:
        pass


class Listener(LoopingProcessAgent):
    class Config(LoopingProcessAgent.Config):
        topic: str = "events"

    config: Config

    def cycle(self) -> None:
        pass


class ThreadListener(LoopingThreadAgent):
    def cycle(self) -> None:
        pass


class Job(BaseProcessAgent):
    class Plugin(BaseProcessAgent.Plugin):
        sensor: SensorPlugin = SensorPlugin()

    plugin: Plugin

    def execute(self) -> None:
        pass


class ThreadJob(BaseThreadAgent):
    def execute(self) -> None:
        pass


class Pool(PoolProcessAgent):
    class Config(PoolProcessAgent.Config):
        agents_entry: list[AgentEntry] = []

    config: Config


if TYPE_CHECKING:
    agent_classes: list[type[AgentProtocol]] = [
        Sensor,
        ThreadSensor,
        Listener,
        ThreadListener,
        Job,
        ThreadJob,
        Pool,
        PoolThreadAgent,
    ]
    entry = AgentEntry(ThreadSensor, "sensor")
