from PyOrchestrate.core.plugins.plugin_protocols import PluginProtocol


class PluginManager:
    def __init__(self, plugins):
        self.plugins = plugins

    def initialize_plugins(self):
        for key, value in self.plugins.__class__.__dict__.items():
            if isinstance(value, PluginProtocol):
                value.initialize()

    def finalize_plugins(self):
        for key, value in self.plugins.__class__.__dict__.items():
            if isinstance(value, PluginProtocol):
                value.finalize()
