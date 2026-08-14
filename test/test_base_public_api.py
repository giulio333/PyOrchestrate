import inspect

from PyOrchestrate.core.base import BaseClass, BaseClassConfig, BaseClassPlugin
from PyOrchestrate.core.base.base import (
    BaseClass as InternalBaseClass,
    BaseClassConfig as InternalBaseClassConfig,
    BaseClassPlugin as InternalBaseClassPlugin,
)


def test_base_classes_are_available_from_public_package():
    assert BaseClass is InternalBaseClass
    assert BaseClassConfig is InternalBaseClassConfig
    assert BaseClassPlugin is InternalBaseClassPlugin


def test_base_class_constructor_only_owns_extension_attributes():
    """Concrete subclasses own config, plugin, and name initialization."""
    assert list(inspect.signature(BaseClass).parameters) == ["kwargs"]
