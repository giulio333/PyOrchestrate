"""
plugin_protocols module.
This module defines the interfaces (protocols) that plugins must implement to be integrated
with the PyOrchestrate framework. The interfaces provide a standardized structure for:
- Plugin initialization (setup).
- Execution of the main plugin logic.
- Finalization (cleanup) after use.

The protocols defined in this module ensure that every plugin adheres to a common contract,
thus promoting consistency and interoperability within the system.
"""

from abc import ABC, abstractmethod


class PluginProtocol(ABC):
    """
    Base protocol for all plugins.

    This protocol defines the essential methods required for managing a plugin's lifecycle:
    - set_owner: Sets the owner (agent/orchestrator) reference for the plugin.
    - initialize: Prepares the plugin by allocating resources or setting up the initial state.
    - finalize: Handles cleanup and resource release.

    `initialize` and `finalize` are abstract and must be implemented.
    `set_owner` has a no-op default, so only the plugins that actually use the
    owner need to override it.
    """

    def set_owner(self, owner):
        """
        Set the owner (agent/orchestrator) reference for the plugin.

        This method is called by the agent or orchestrator during initialization to provide
        the plugin with access to the owner instance.

        The default implementation ignores the owner: a plugin that never needs
        to reach back to the agent or the orchestrator does not have to override
        it. Requiring an override produced six copies of
        ``return super().set_owner(owner)`` across the ZeroMQ plugins, all of
        them delegating to a method whose body was ``pass``.

        Args:
            owner: The agent or orchestrator instance that owns this plugin
        """

    @abstractmethod
    def initialize(self):
        """
        Initializes the plugin.

        Called only once at the time of plugin registration.
        Use this method to set up the necessary resources for subsequent execution.
        """
        pass

    @abstractmethod
    def finalize(self):
        """
        Finalizes the plugin.

        Called at the end of the plugin lifecycle to release resources, close connections,
        or perform any other cleanup operations.
        """
        pass
