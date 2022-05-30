
from myne.plugins import ProtocolPlugin
from myne.decorators import *

class TeleportPlugin(ProtocolPlugin):
    
    commands = {
        "teleport": "commandTeleport",
        "goto": "commandGoto",
        "tp": "commandGoto",
    }
    
    def commandTeleport(self, parts):
        "/teleport x y z - Teleports you to coords. Note y is up."
        try:
            x = int(parts[1])
            y = int(parts[2])
            z = int(parts[3])
            self.client.teleportTo(x, y, z)
        except (IndexError, ValueError):
            self.client.sendServerMessage("Usage: /teleport x y z")
    
    @username_command
    def commandGoto(self, user):
        "/goto username - Teleports you to the user's location."
        x = user.x >> 5
        y = user.y >> 5
        z = user.z >> 5
        if user.world == self.client.world:
            self.client.teleportTo(x, y, z)
        else:
            if self.client.canEnter(user.world):
                self.client.changeToWorld(user.world.id, position=(x, y, z))
            else:
                self.client.sendServerMessage("Sorry, that world is private.")
    