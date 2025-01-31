from .communication_plugins import CommunicationPlugin


class PluginManager:
    """
    Plugin manager for the agent.

    Attributes:
        com (CommunicationPlugin): Communication plugin.

    Methods:
        register_com_plugin: Register the communication plugin.
        unregister_com_plugin: Unregister the communication plugin.
    """

    def __init__(self):
        self.com = None

    def register(self, plugin: CommunicationPlugin):
        """
        Register and initialize the communication plugin.

        Args:
            plugin (CommunicationPlugin): Communication plugin to register.
        """
        self.com = plugin
        self.com.initialize()

    def unregister(self):
        """
        Unregister and finalize the communication plugin.

        Raises:
            AttributeError: If the communication plugin is not registered.
        """
        if not self.com:
            raise AttributeError("Communication plugin not registered.")

        self.com.finalize()
        self.com = None
