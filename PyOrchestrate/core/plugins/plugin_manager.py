"""Module for managing plugin initialization and finalization."""

from collections import OrderedDict
import inspect

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
        self._owner = None  # Reference to the owner (agent/orchestrator)

        # Extract and cache plugin instances during initialization for efficiency
        self._plugin_instances: list[tuple[str, PluginProtocol]] = (
            self._extract_plugin_instances()
        )

    def _extract_plugin_instances(self):
        plugins = self.plugins
        merged: OrderedDict[str, PluginProtocol] = OrderedDict()

        def is_plugin_instance(val) -> bool:
            if val is None:
                return False
            if inspect.isfunction(val) or inspect.ismethod(val) or inspect.isclass(val):
                return False
            return True

        # 1) Class attributes (default/legacy) — base layer
        for key, value in plugins.__class__.__dict__.items():
            if key.startswith("_"):
                continue
            if is_plugin_instance(value):
                merged[key] = value

        # 2) Instance attributes — override class
        for key, value in vars(plugins).items():
            if key.startswith("_"):
                continue
            if is_plugin_instance(value):
                merged[key] = value  # override

        # 3) _custom_attr (iniezioni dinamiche) — override
        if hasattr(plugins, "_custom_attr"):
            for key, value in plugins._custom_attr.items():
                if key.startswith("_"):
                    continue
                if is_plugin_instance(value):
                    merged[key] = value  # override

        # Converte in lista di tuple
        return list(merged.items())

    def set_owner(self, owner):
        """
        Set the owner (agent/orchestrator) reference for plugins that need it.

        This is called by the agent or orchestrator during initialization to provide
        plugins with access to the owner instance.

        Args:
            owner: The agent or orchestrator instance that owns these plugins
        """
        self._owner = owner

        # Pass owner reference to plugins using the cached plugin instances
        for name, plugin_instance in self._plugin_instances:
            try:
                plugin_instance.set_owner(owner)
            except Exception as e:
                self._log_error(
                    f"Failed to set owner reference for plugin '{name}': {e}"
                )

    def plugin_info(self):
        """
        Log information about all managed plugins.

        This method iterates through all cached plugin instances and logs their names and types.
        """
        if self._owner:
            self._owner.logger.info(
                f"PluginManager: Managing {len(self._plugin_instances)} plugins:"
            )
            for name, plugin_instance in self._plugin_instances:
                self._owner.logger.info(
                    f" - Plugin '{name}': {type(plugin_instance).__name__}"
                )

    def _log_error(self, message):
        """Helper method to log errors using owner's logger or print as fallback."""
        if self._owner:
            self._owner.logger.error(message)
        else:
            print(f"PluginManager ERROR: {message}")

    def initialize_plugins(self):
        """
        Initialize all plugins using the cached plugin instances.

        Calls the initialize method on each plugin that has it.
        """
        if self._owner:
            self._owner.logger.debug(
                f"PluginManager: Initializing {len(self._plugin_instances)} plugins"
            )

        for name, plugin_instance in self._plugin_instances:
            try:
                if self._owner:
                    self._owner.logger.debug(
                        f"PluginManager: Initializing plugin '{name}' ({type(plugin_instance).__name__})"
                    )
                plugin_instance.initialize()
                if self._owner:
                    self._owner.logger.debug(
                        f"PluginManager: Plugin '{name}' initialized successfully"
                    )
            except Exception as e:
                self._log_error(f"Failed to initialize plugin '{name}': {e}")

    def finalize_plugins(self):
        """
        Finalize all plugins using the cached plugin instances.

        Calls the finalize method on each plugin that has it.
        """
        for name, plugin_instance in self._plugin_instances:
            try:
                plugin_instance.finalize()
            except Exception as e:
                self._log_error(f"Failed to finalize plugin '{name}': {e}")

    def get_plugin(self, plugin_name: str) -> PluginProtocol | None:
        """
        Get a specific plugin instance by name.

        Args:
            plugin_name: The name of the plugin to retrieve.

        Returns:
            The plugin instance if found, otherwise None.
        """
        for name, plugin_instance in self._plugin_instances:
            if name == plugin_name:
                return plugin_instance
        return None
