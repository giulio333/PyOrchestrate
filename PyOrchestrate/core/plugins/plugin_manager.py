"""Module for managing plugin initialization and finalization."""

from PyOrchestrate.core.plugins.plugin_protocols import PluginProtocol


class PluginManager:
    """
    Class responsible for managing plugins, providing methods for initialization and finalization.
    """

    def __init__(self, plugins):
        """
        Initialize the PluginManager with the provided plugins instance.

        Parameters:
        plugins: An object containing plugin instances defined as attributes.
        """
        self.plugins = plugins

    def initialize_plugins(self):
        """
        Initialize all plugins that implement the `PluginProtocol`.

        Iterates over the `plugin` attributes and calls the initialize method on each plugin.
        """
        for key, value in self.plugins.__class__.__dict__.items():
            if isinstance(value, PluginProtocol):
                value.initialize()

    def finalize_plugins(self):
        """
        Finalize all plugins that implement the `PluginProtocol`.

        Iterates over the `plugin` attributes and calls the finalize method on each plugin.
        """
        for key, value in self.plugins.__class__.__dict__.items():
            if isinstance(value, PluginProtocol):
                value.finalize()
