
from myne.plugins import ProtocolPlugin
from myne.decorators import *

class CorePlugin(ProtocolPlugin):
    
    commands = {
        "pluginload": "commandPluginload",
        "pll": "commandPluginload",
        "pluginunload": "commandPluginunload",
        "plu": "commandPluginunload",
        "pluginreload": "commandPluginreload",
        "plr": "commandPluginreload",
    }
    
    @admin_only
    @only_string_command("plugin name")
    def commandPluginreload(self, plugin_name):
        try:
            self.client.factory.unloadPlugin(plugin_name)
            self.client.factory.loadPlugin(plugin_name)
        except IOError:
            self.client.sendServerMessage("No such plugin '%s'." % plugin_name)
        else:
            self.client.sendServerMessage("Plugin '%s' reloaded." % plugin_name)
    
    @admin_only
    @only_string_command("plugin name")
    def commandPluginload(self, plugin_name):
        try:
            self.client.factory.loadPlugin(plugin_name)
        except IOError:
            self.client.sendServerMessage("No such plugin '%s'." % plugin_name)
        else:
            self.client.sendServerMessage("Plugin '%s' loaded." % plugin_name)
    
    @admin_only
    @only_string_command("plugin name")
    def commandPluginunload(self, plugin_name):
        try:
            self.client.factory.unloadPlugin(plugin_name)
        except IOError:
            self.client.sendServerMessage("No such plugin '%s'." % plugin_name)
        else:
            self.client.sendServerMessage("Plugin '%s' unloaded." % plugin_name)
    