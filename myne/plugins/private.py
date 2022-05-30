
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class PrivatePlugin(ProtocolPlugin):
    
    commands = {
        "private": "commandPrivate",
        "public": "commandPublic",
    }
    
    @op_only
    def commandPrivate(self, parts):
        "/private - Removes from worlds lists and only allows in writers."
        self.client.world.private = True
        self.client.sendWorldMessage("This world is now private.")
        self.client.sendServerMessage("%s is now private." % self.client.world.id)
    
    @op_only
    def commandPublic(self, parts):
        "/public - Reverses the effects of /private on the world"
        self.client.world.private = False
        self.client.sendWorldMessage("This world is now public.")
        self.client.sendServerMessage("%s is now public." % self.client.world.id)
    