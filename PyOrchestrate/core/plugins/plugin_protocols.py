"""
Plugin protocols module.

This module defines the core protocols (interfaces) for the plugin system in PyOrchestrate.
Plugin protocols provide a standardized way to define and implement plugins, ensuring
consistency and interoperability across the entire framework.

The module implements two main protocols:

- Plugin: The base protocol that all plugins must implement, defining the basic
  lifecycle methods (initialize, execute, finalize).
  
- CommunicationPlugin: A specialized protocol for plugins that handle communication,
  extending the base Plugin protocol with additional messaging capabilities.

These protocols serve as contracts that plugin implementations must fulfill, making
the plugin system both extensible and maintainable. By following these protocols,
developers can create new plugins that seamlessly integrate with the PyOrchestrate
framework.

Example:
    To create a new plugin, implement either the Plugin or CommunicationPlugin
    protocol based on your needs:

    class MyPlugin(Plugin):
        def initialize(self):
            # Setup code
            pass
"""

from typing import Protocol


class Plugin(Protocol):
    """
    Protocol for all plugins.

    This protocol provides a common interface for plugin lifecycle management, defining
    the essential methods that a plugin must implement.

    Methods:
        initialize: Initializes the plugin.
        execute: Executes the plugin's core logic.
        finalize: Finalizes the plugin.
    """

    def initialize(self):
        """
        Initializes the plugin.

        This method is called once when the plugin is registered.
        """
        pass

    def execute(self):
        """
        Executes the plugin's core logic.

        This method is called during the agent's execution.
        """
        pass

    def finalize(self):
        """
        Finalizes the plugin.

        This method is called once when the plugin is unregistered.
        """
        pass


class CommunicationPlugin(Plugin):
    """
    Protocol for communication plugins.

    This protocol provides a common interface for communication plugins, defining
    the essential methods that a communication plugin must implement.

    Methods:
        send: Sends a message.
        receive: Receives a message.
    """

    def send(self, message):
        """
        Sends a message.
        """
        pass

    def receive(self):
        """
        Receives a message.
        """
        pass
