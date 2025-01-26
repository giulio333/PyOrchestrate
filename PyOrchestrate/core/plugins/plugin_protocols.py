"""
Plugin protocols module.
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
