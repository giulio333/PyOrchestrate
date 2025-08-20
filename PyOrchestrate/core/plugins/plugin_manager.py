"""Module for managing plugin initialization and finalization."""

from PyOrchestrate.core.plugins.plugin_protocols import PluginProtocol
from PyOrchestrate.core.base.base import BaseClassPlugin


class PluginManager:
    """
    Class responsible for managing plugins, providing methods for initialization and finalization.
    """

    def __init__(self, plugins: BaseClassPlugin):
        """
        Initialize the PluginManager with the provided plugins instance.

        Parameters:
            plugins: An object containing plugin instances defined as attributes.
        """
        self.plugins: BaseClassPlugin = plugins
        self._agent = None  # Reference to the agent (set when agent initializes)

    def set_agent(self, agent):
        """
        Set the agent reference for plugins that need it.

        This is called by the agent during initialization to provide
        plugins with access to the agent instance.

        Args:
            agent: The agent instance that owns these plugins
        """
        self._agent = agent

        # Pass agent reference to plugins that need it
        # Check both class attributes (common pattern) and instance attributes
        for key, value in self.plugins.__class__.__dict__.items():
            if isinstance(value, PluginProtocol) and hasattr(value, "set_agent"):
                value.set_agent(agent)

        for key, value in vars(self.plugins).items():
            if isinstance(value, PluginProtocol) and hasattr(value, "set_agent"):
                value.set_agent(agent)

    def initialize_plugins(self):
        """
        Initialize all plugins that implement the `PluginProtocol`.

        Iterates over the `plugin` attributes and calls the initialize method on each plugin.
        """
        # First check class attributes (legacy support)
        for key, value in self.plugins.__class__.__dict__.items():
            if isinstance(value, PluginProtocol):
                value.initialize()

        # Then check instance attributes (modern approach)
        for key, value in vars(self.plugins).items():
            if isinstance(value, PluginProtocol):
                value.initialize()

    def finalize_plugins(self):
        """
        Finalize all plugins that implement the `PluginProtocol`.

        Iterates over the `plugin` attributes and calls the finalize method on each plugin.
        """
        # First check class attributes (legacy support)
        for key, value in self.plugins.__class__.__dict__.items():
            if isinstance(value, PluginProtocol):
                value.finalize()

        # Then check instance attributes (modern approach)
        for key, value in vars(self.plugins).items():
            if isinstance(value, PluginProtocol):
                value.finalize()
