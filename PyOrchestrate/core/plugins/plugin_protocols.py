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


class Plugin:
    """
    Base protocol for all plugins.

    This protocol defines the essential methods required for managing a plugin's lifecycle:
    - initialize: Prepares the plugin by allocating resources or setting up the initial state.
    - execute: Executes the main logic of the plugin.
    - finalize: Handles cleanup and resource release.

    Developers must implement these methods to ensure proper integration with the system.
    """

    def initialize(self):
        """
        Initializes the plugin.

        Called only once at the time of plugin registration.
        Use this method to set up the necessary resources for subsequent execution.
        """
        pass

    def finalize(self):
        """
        Finalizes the plugin.

        Called at the end of the plugin lifecycle to release resources, close connections,
        or perform any other cleanup operations.
        """
        pass
