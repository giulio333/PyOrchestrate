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
        self._owner = None  # Reference to the owner (agent/orchestrator)

        # Extract and cache plugin instances during initialization for efficiency
        self._plugin_instances: list[tuple[str, PluginProtocol]] = (
            self._extract_plugin_instances()
        )

    def _extract_plugin_instances(self):
        """
        Extract all plugin instances from the plugins object and create an efficient data structure.

        Returns:
            List of tuples (name, plugin_instance) for all valid plugins.
        """
        plugin_instances = []

        # Check class attributes (legacy support for agents with Plugin inner classes)
        for key, value in self.plugins.__class__.__dict__.items():
            if (
                not key.startswith("_")
                and value is not None
                and hasattr(value, "__class__")
            ):
                plugin_instances.append((key, value))

        # Collect all possible plugin names from both instance vars and custom attributes
        all_possible_keys = set()

        # Add instance attribute keys
        for key in vars(self.plugins).keys():
            if not key.startswith("_"):
                all_possible_keys.add(key)

        # Add custom attribute keys (from kwargs)
        if hasattr(self.plugins, "_custom_attr"):
            for key in self.plugins._custom_attr.keys():
                if not key.startswith("_"):
                    all_possible_keys.add(key)

        for key in all_possible_keys:
            try:
                value = getattr(self.plugins, key)
                if value is not None and hasattr(value, "__class__"):
                    plugin_instances.append((key, value))
            except AttributeError:
                # Skip keys that don't resolve to actual attributes
                pass

        return plugin_instances

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

    # def __getattribute__(self, name):
    #     """
    #     Provide transparent access to plugin instances.

    #     This method allows accessing plugins directly as attributes of the PluginManager,
    #     e.g., plugin_manager.heartbeat will return the heartbeat plugin instance.
    #     """
    #     # First try to get standard PluginManager attributes
    #     try:
    #         return object.__getattribute__(self, name)
    #     except AttributeError:
    #         pass

    #     # Then try to get plugin attributes from the underlying BaseClassPlugin
    #     plugins = object.__getattribute__(self, "plugins")
    #     if plugins is not None:
    #         try:
    #             return getattr(plugins, name)
    #         except AttributeError:
    #             pass

    #     # If not found, raise AttributeError
    #     raise AttributeError(
    #         f"'{self.__class__.__name__}' object has no attribute '{name}'"
    #     )
