"""
plugin_manager module.
This module defines the PluginManager class, responsible for registering, initializing, and
finalizing communication plugins (which must implement the CommunicationPlugin protocol).
PluginManager centralizes the management of the communication plugin's lifecycle, facilitating
setup and cleanup operations within the application.
"""

from .communication_plugins import CommunicationPlugin


class PluginManager:
    """
    Manages the lifecycle of communication plugins.

    Responsible for registering (initializing) and unregistering (finalizing) the
    communication plugin, ensuring that operations are performed safely.

    Attributes:
        com (CommunicationPlugin): The currently registered communication plugin instance.

    Methods:
        register: Registers and initializes the communication plugin.
        unregister: Finalizes and removes the registered communication plugin.
    """

    def __init__(self):
        self.com = None

    def register(self, plugin: CommunicationPlugin):
        """
        Registers and initializes the communication plugin.

        Associates the plugin instance with the manager and calls its initialize method
        to set up the necessary resources.

        Args:
            plugin (CommunicationPlugin): The communication plugin instance to register.
        """
        self.com = plugin
        self.com.initialize()

    def unregister(self):
        """
        Finalizes and removes the registered communication plugin.

        Calls the finalize method of the plugin to release any used resources and removes the reference.
        Raises an exception if no plugin is currently registered.

        Raises:
            AttributeError: If no communication plugin has been registered.
        """
        if not self.com:
            raise AttributeError("Communication plugin not registered.")

        self.com.finalize()
        self.com = None
