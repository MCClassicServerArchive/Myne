
from myne.plugins import ProtocolPlugin
from myne.decorators import *

class FetchPlugin(ProtocolPlugin):
    
    commands = {
        "fetch": "commandFetch",
    }
    
    @op_only
    @username_command
    def commandFetch(self, user):
        "/fetch username - Teleports a user to be where you are"
        
        # Shift the locations right to make them into block coords
        rx = self.client.x >> 5
        ry = self.client.y >> 5
        rz = self.client.z >> 5
        
        if user.world == self.client.world:
            user.teleportTo(rx, ry, rz)
        else:
            if self.client.isAdmin():
                user.changeToWorld(self.client.world.id, position=(rx, ry, rz))
            else:
                self.client.sendServerMessage("%s cannot be fetched from '%s'" % (self.client.username, user.world.id))
                return
        user.sendServerMessage("You have been fetched by %s" % self.client.username)
    