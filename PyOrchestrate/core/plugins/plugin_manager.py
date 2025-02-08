"""
plugin_manager module.
This module defines the PluginManager class, responsible for registering, initializing, and
finalizing communication plugins (which must implement the CommunicationPlugin protocol).
PluginManager centralizes the management of the communication plugin's lifecycle, facilitating
setup and cleanup operations within the application.
"""

from .plugin_protocols import CommunicationPlugin, Plugin


class PluginManager:
    """
    Manages the lifecycle of communication plugins.

    Responsible for registering (initializing) and unregistering (finalizing) the
    communication plugin, ensuring that operations are performed safely.

    Example:
        >>> plugin_manager = PluginManager()
        >>> zmq_plugin = ZeroMQPubSub("tcp://localhost:5555", zmq.PUB)
        >>> plugin_manager.register(zmq_plugin)

    Attributes:
        com (CommunicationPlugin): The currently registered communication plugin instance.

    Methods:
        register: Registers and initializes the communication plugin.
        unregister: Finalizes and removes the registered communication plugin.
    """

    def __init__(self):
        self.com: CommunicationPlugin = CommunicationPlugin()

    def register(self, plugin: Plugin):
        """
        Registers and initializes the communication plugin.

        Associates the plugin instance with the manager and calls its initialize method
        to set up the necessary resources.

        Args:
            plugin (CommunicationPlugin): The communication plugin instance to register.
        """
        self.com.zmq = plugin
        self.com.zmq.initialize()

    def unregister(self):
        """
        Finalizes and removes the registered communication plugin.

        Calls the finalize method of the plugin to release any used resources and removes the reference.
        Raises an exception if no plugin is currently registered.

        Raises:
            AttributeError: If no communication plugin has been registered.
        """
        if not self.com.zmq:
            raise AttributeError("Communication plugin not registered.")

        self.com.zmq.finalize()
