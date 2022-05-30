
from myne.plugins import ProtocolPlugin
from myne.decorators import *

class OverloadPlugin(ProtocolPlugin):
    
    commands = {
        "overload": "commandOverload",
    }
    
    @admin_only
    @username_command
    def commandOverload(self, client):
        "/overload username - Sends the user's client a massive fake map."
        client.sendOverload()
        self.client.sendServerMessage("Overload sent to %s" % client.username)
    