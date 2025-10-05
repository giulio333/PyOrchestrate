---
title: Plugin Manager
editLink: true
---

# Plugin Manager

The **Plugin Manager** in PyOrchestrate is a core utility responsible for managing plugin initialization, finalization, and lifecycle. It provides a centralized approach to handle plugins within agents and orchestrators, ensuring proper resource management and plugin coordination.

## Overview

The Plugin Manager is responsible for:
- Managing plugin instances across the application lifecycle
- Handling plugin initialization and finalization
- Providing plugin discovery and retrieval mechanisms
- Managing owner references for plugins that need access to their parent agent or orchestrator

## Class Structure

The `PluginManager` class is defined in `PyOrchestrate.core.plugins.plugin_manager` and manages plugins for agents and orchestrators.

### Constructor

```python
def __init__(self, plugins: BaseClassPlugin):
    """
    Initialize the PluginManager with the provided plugins instance.

    Parameters:
        plugins: An object containing plugin instances defined as attributes.
    """
```

The constructor takes a `BaseClassPlugin` instance that contains the plugin definitions and automatically extracts all plugin instances during initialization for efficient access.

### Key Attributes

- `plugins`: The BaseClassPlugin instance containing plugin definitions
- `_owner`: Reference to the owner (agent/orchestrator) that owns this plugin manager
- `_plugin_instances`: Cached list of (name, plugin_instance) tuples for efficient access

## Plugin Discovery and Extraction

The Plugin Manager uses a sophisticated plugin extraction mechanism that supports multiple plugin definition patterns:

### Plugin Definition Hierarchy

The plugin extraction follows a specific hierarchy where later definitions override earlier ones:

1. **Class Attributes** (base layer): Default plugins defined at the class level
2. **Instance Attributes** (override): Plugins defined on the instance 
3. **Custom Attributes** (highest priority): Dynamic plugins injected via `_custom_attr`

```python
def _extract_plugin_instances(self):
    """Extract plugin instances from the plugins object following priority order."""
    plugins = self.plugins
    merged: OrderedDict[str, PluginProtocol] = OrderedDict()

    # 1) Class attributes (default/legacy) — base layer
    for key, value in plugins.__class__.__dict__.items():
        if key.startswith("_"):
            continue
        if is_plugin_instance(value):
            merged[key] = value

    # 2) Instance attributes — override class
    for key, value in vars(plugins).items():
        if key.startswith("_"):
            continue
        if is_plugin_instance(value):
            merged[key] = value  # override

    # 3) _custom_attr (dynamic injections) — override
    if hasattr(plugins, "_custom_attr"):
        for key, value in plugins._custom_attr.items():
            if key.startswith("_"):
                continue
            if is_plugin_instance(value):
                merged[key] = value  # override

    return list(merged.items())
```

### Plugin Instance Validation

The manager validates whether an object is a valid plugin instance:

```python
def is_plugin_instance(val) -> bool:
    if val is None:
        return False
    if inspect.isfunction(val) or inspect.ismethod(val) or inspect.isclass(val):
        return False
    return True
```

This ensures that only actual plugin instances (not classes, functions, or methods) are managed.

## Core Methods

### Owner Management

The Plugin Manager provides owner reference management for plugins that need access to their parent agent or orchestrator:

```python
def set_owner(self, owner):
    """
    Set the owner (agent/orchestrator) reference for plugins that need it.
    
    This is called by the agent or orchestrator during initialization to provide
    plugins with access to the owner instance.
    """
    self._owner = owner

    # Pass owner reference to plugins using the cached plugin instances
    for name, plugin_instance in self._plugin_instances:
        try:
            plugin_instance.set_owner(owner)
        except Exception as e:
            self._log_error(f"Failed to set owner reference for plugin '{name}': {e}")
```

### Plugin Information and Logging

```python
def plugin_info(self):
    """
    Log information about all managed plugins.
    
    This method iterates through all cached plugin instances and logs their names and types.
    """
    if self._owner:
        self._owner.logger.info(f"PluginManager: Managing {len(self._plugin_instances)} plugins:")
        for name, plugin_instance in self._plugin_instances:
            self._owner.logger.info(f" - Plugin '{name}': {type(plugin_instance).__name__}")
```

### Plugin Lifecycle Management

#### Initialization

```python
def initialize_plugins(self):
    """
    Initialize all plugins using the cached plugin instances.
    
    Calls the initialize method on each plugin that has it.
    """
    if self._owner:
        self._owner.logger.debug(f"PluginManager: Initializing {len(self._plugin_instances)} plugins")

    for name, plugin_instance in self._plugin_instances:
        try:
            if self._owner:
                self._owner.logger.debug(f"PluginManager: Initializing plugin '{name}' ({type(plugin_instance).__name__})")
            plugin_instance.initialize()
            if self._owner:
                self._owner.logger.debug(f"PluginManager: Plugin '{name}' initialized successfully")
        except Exception as e:
            self._log_error(f"Failed to initialize plugin '{name}': {e}")
```

#### Finalization

```python
def finalize_plugins(self):
    """
    Finalize all plugins using the cached plugin instances.
    
    Calls the finalize method on each plugin that has it.
    """
    for name, plugin_instance in self._plugin_instances:
        try:
            plugin_instance.finalize()
        except Exception as e:
            self._log_error(f"Failed to finalize plugin '{name}': {e}")
```

### Plugin Retrieval

```python
def get_plugin(self, plugin_name: str) -> PluginProtocol | None:
    """
    Get a specific plugin instance by name.

    Args:
        plugin_name: The name of the plugin to retrieve.

    Returns:
        The plugin instance if found, otherwise None.
    """
    for name, plugin_instance in self._plugin_instances:
        if name == plugin_name:
            return plugin_instance
    return None
```

## Error Handling

The Plugin Manager includes robust error handling with proper logging:

```python
def _log_error(self, message):
    """Helper method to log errors using owner's logger or print as fallback."""
    if self._owner:
        self._owner.logger.error(message)
    else:
        print(f"PluginManager ERROR: {message}")
```

This method ensures that errors are properly logged through the owner's logging system when available, or falls back to standard output when no owner is set.

## Usage Examples

### Basic Usage in an Agent

```python
from PyOrchestrate.core.plugins.plugin_manager import PluginManager
from PyOrchestrate.core.base.base import BaseClassPlugin

# Define your plugins
class MyPlugins(BaseClassPlugin):
    communication_plugin = ZeroMQPubSubPlugin()
    validation_plugin = ValidationPlugin()

# Create plugin manager
plugins = MyPlugins()
plugin_manager = PluginManager(plugins)

# Set owner reference (typically done by agent/orchestrator)
plugin_manager.set_owner(my_agent)

# Initialize all plugins
plugin_manager.initialize_plugins()

# Get plugin information
plugin_manager.plugin_info()

# Retrieve a specific plugin
comm_plugin = plugin_manager.get_plugin("communication_plugin")

# Finalize when done
plugin_manager.finalize_plugins()
```

### Dynamic Plugin Injection

```python
# Example of dynamic plugin injection via _custom_attr
plugins = MyPlugins()
plugins._custom_attr = {
    "dynamic_plugin": CustomDynamicPlugin(),
    "runtime_plugin": RuntimePlugin()
}

plugin_manager = PluginManager(plugins)
# The dynamic plugins will be automatically discovered and managed
```

### Plugin Override Pattern

```python
class BasePlugins(BaseClassPlugin):
    # Default plugin at class level
    storage_plugin = FileStoragePlugin()

class ProductionPlugins(BasePlugins):
    def __init__(self):
        super().__init__()
        # Override with production plugin at instance level
        self.storage_plugin = DatabaseStoragePlugin()

# The instance-level plugin will override the class-level one
production_plugins = ProductionPlugins()
plugin_manager = PluginManager(production_plugins)
```

## Integration with PyOrchestrate Components

### Agent Integration

Agents use the Plugin Manager to manage their communication and utility plugins:

```python
from PyOrchestrate.core.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(config)
        # Plugin manager is automatically created with agent's plugins
        # Owner reference is set during agent initialization
        
        # Access plugins through the manager
        comm_plugin = self.plugin_manager.get_plugin("communication")
        
    def initialize(self):
        super().initialize()
        # Plugins are automatically initialized
        self.plugin_manager.plugin_info()  # Log plugin information
```

### Orchestrator Integration

Orchestrators similarly use the Plugin Manager for their plugin ecosystem:

```python
from PyOrchestrate.core.orchestrator.base_orchestrator import BaseOrchestrator

class MyOrchestrator(BaseOrchestrator):
    def __init__(self, config):
        super().__init__(config)
        # Plugin manager handles orchestrator plugins
        
    def start(self):
        super().start()
        # All plugins are properly initialized before orchestrator starts
```

## Plugin Protocol Compliance

All plugins managed by the Plugin Manager must implement the `PluginProtocol` interface:

```python
from PyOrchestrate.core.plugins.plugin_protocols import PluginProtocol

class MyCustomPlugin(PluginProtocol):
    def initialize(self):
        """Initialize plugin resources"""
        pass
    
    def finalize(self):
        """Cleanup plugin resources"""
        pass
    
    def set_owner(self, owner):
        """Set reference to owning agent/orchestrator"""
        self.owner = owner
```

## Performance Considerations

### Caching Strategy

The Plugin Manager caches plugin instances during initialization to avoid repeated extraction:

- Plugin instances are extracted once during `__init__`
- Cached instances are reused for all operations
- This provides O(1) access time for plugin operations

### Memory Management

- Plugin instances are held in memory for the lifetime of the Plugin Manager
- Proper finalization ensures resources are cleaned up
- The manager holds references but doesn't control plugin lifecycle beyond init/finalize

## Best Practices

### Plugin Design

1. **Implement Error Handling**: Always handle exceptions in initialize() and finalize()
2. **Resource Management**: Properly acquire and release resources
3. **Owner Usage**: Use the owner reference responsibly and check for None
4. **Logging**: Use the owner's logger when available

### Plugin Manager Usage

1. **Initialization Order**: Always set owner before initializing plugins
2. **Error Monitoring**: Monitor plugin manager logs for initialization failures
3. **Graceful Shutdown**: Always call finalize_plugins() before shutdown
4. **Plugin Naming**: Use descriptive names for plugin attributes

### Testing

```python
import unittest
from unittest.mock import Mock

class TestPluginManager(unittest.TestCase):
    def setUp(self):
        self.mock_plugins = Mock()
        self.mock_plugins.test_plugin = Mock()
        self.manager = PluginManager(self.mock_plugins)
    
    def test_plugin_extraction(self):
        # Test that plugins are properly extracted
        self.assertEqual(len(self.manager._plugin_instances), 1)
        self.assertEqual(self.manager._plugin_instances[0][0], "test_plugin")
    
    def test_plugin_initialization(self):
        # Test plugin initialization
        self.manager.initialize_plugins()
        self.mock_plugins.test_plugin.initialize.assert_called_once()
```

The Plugin Manager is a foundational utility that enables PyOrchestrate's modular architecture by providing consistent plugin lifecycle management across agents and orchestrators.