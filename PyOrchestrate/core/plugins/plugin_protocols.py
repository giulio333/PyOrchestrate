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

from typing import Protocol


class Plugin(Protocol):
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


class CommunicationPlugin(Plugin):
    """
    Extended protocol for communication plugins.

    This protocol, which extends Plugin, adds specific methods for sending and receiving
    messages (e.g., via sockets or PyZMQ). It is designed to standardize communication
    operations among system components.

    Additional methods:
        - setsockopt: Configures socket options.
    """

    def setsockopt(self, option, value):
        """
        Configures a socket option.

        Sets a specific option for the socket, useful for customized configurations.
        Refer to the PyZMQ documentation for more details on available options.

        Args:
            option: The option to configure (e.g., zmq.SUBSCRIBE).
            value: The value to assign to the option.
        """
        pass
