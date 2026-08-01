from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyOrchestrate.core.agent.pool_agent import PoolProcessAgent, PoolThreadAgent

__all__ = [
    "BaseThreadAgent",
    "BaseProcessAgent",
    "BaseAgent",
    "AgentProtocol",
    "LoopingAgent",
    "LoopingProcessAgent",
    "LoopingThreadAgent",
    "PeriodicAgent",
    "PeriodicProcessAgent",
    "PeriodicThreadAgent",
    "PoolProcessAgent",
    "PoolThreadAgent",
]

from PyOrchestrate.core.agent.base_agent import (
    BaseThreadAgent,
    BaseProcessAgent,
    BaseAgent,
    AgentProtocol,
)
from PyOrchestrate.core.agent.looping_agent import (
    LoopingAgent,
    LoopingProcessAgent,
    LoopingThreadAgent,
)
from PyOrchestrate.core.agent.periodic_agent import (
    PeriodicAgent,
    PeriodicProcessAgent,
    PeriodicThreadAgent,
)

# The pool agents cannot be imported eagerly: pool_agent imports Orchestrator,
# which imports agent.base_agent, so importing PyOrchestrate.core.orchestrator
# first would hit a partially initialized module. Resolving them on attribute
# access (PEP 562) defers that import until the package is fully loaded, which
# keeps them importable from here as __all__ advertises.
_LAZY_AGENTS = {
    "PoolProcessAgent": "PyOrchestrate.core.agent.pool_agent",
    "PoolThreadAgent": "PyOrchestrate.core.agent.pool_agent",
}


def __getattr__(name: str):
    """Resolve the pool agents on first access."""
    module_name = _LAZY_AGENTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from importlib import import_module

    attribute = getattr(import_module(module_name), name)
    globals()[name] = attribute  # Cache so later lookups skip __getattr__
    return attribute


def __dir__():
    """List the eager names plus the lazily resolved pool agents."""
    return sorted(set(globals()) | set(_LAZY_AGENTS))
