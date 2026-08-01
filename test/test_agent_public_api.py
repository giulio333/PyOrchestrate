import subprocess
import sys

import pytest

import PyOrchestrate.core.agent as agent_package
from PyOrchestrate.core.agent.pool_agent import (
    PoolProcessAgent as InternalPoolProcessAgent,
    PoolThreadAgent as InternalPoolThreadAgent,
)


@pytest.mark.parametrize("name", agent_package.__all__)
def test_every_advertised_name_is_importable(name):
    """Every name in __all__ resolves, so `import *` cannot fail."""
    assert getattr(agent_package, name) is not None


def test_pool_agents_are_available_from_public_package():
    assert agent_package.PoolProcessAgent is InternalPoolProcessAgent
    assert agent_package.PoolThreadAgent is InternalPoolThreadAgent


def test_pool_agents_are_listed_by_dir():
    """The lazily resolved names stay discoverable via dir()."""
    listed = dir(agent_package)
    assert "PoolProcessAgent" in listed
    assert "PoolThreadAgent" in listed


def test_unknown_attribute_still_raises():
    with pytest.raises(AttributeError):
        agent_package.NoSuchAgent


def test_pool_agents_resolve_when_orchestrator_is_imported_first():
    """
    Importing the orchestrator first must not break the pool agents.

    The pool agents can only be resolved lazily: pool_agent imports
    Orchestrator, which imports agent.base_agent, so an eager import raises
    ImportError on a partially initialized module for this order. Run it in a
    subprocess, since within the test session the modules are already cached.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import PyOrchestrate.core.orchestrator\n"
            "from PyOrchestrate.core.agent import PoolProcessAgent, PoolThreadAgent\n"
            "print(PoolProcessAgent.__name__, PoolThreadAgent.__name__)",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "PoolProcessAgent PoolThreadAgent" in result.stdout
