"""The names PyOrchestrate.core.orchestrator advertises must resolve."""

import pytest

import PyOrchestrate.core.orchestrator as orchestrator_package
from PyOrchestrate.core.orchestrator.orchestrator import (
    OrchestratorConfig as InternalOrchestratorConfig,
    OrchestratorPlugin as InternalOrchestratorPlugin,
)


@pytest.mark.parametrize("name", orchestrator_package.__all__)
def test_every_advertised_name_is_importable(name):
    """Every name in __all__ resolves, so `import *` cannot fail."""
    assert getattr(orchestrator_package, name) is not None


def test_config_and_plugin_are_available_from_the_package():
    """The two classes every user needs were reachable only by deep import."""
    assert orchestrator_package.OrchestratorConfig is InternalOrchestratorConfig
    assert orchestrator_package.OrchestratorPlugin is InternalOrchestratorPlugin
