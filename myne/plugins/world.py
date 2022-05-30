
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class WorldPlugin(ProtocolPlugin):
    
    commands = {
        "status": "commandStatus",
        "setspawn": "commandSetspawn",
        "where": "commandWhere",
    }
    
    def commandStatus(self, parts):
        "/status - Returns info about the current world"
        self.client.sendServerMessage("World: %s (%sx%sx%s)" % (self.client.world.id, self.client.world.x, self.client.world.y, self.client.world.z))
        self.client.sendServerMessage(
            (self.client.world.all_write and "Unlocked" or "Locked") + ", " + \
            (self.client.world.admin_blocks and "Admin Blocks On" or "Admin Blocks Off") + ", " + \
            (self.client.world.private and "Private" or "Public") + ","
        )
        self.client.sendServerMessage(
            (self.client.world.highlight_ops and "Ops Highlighted" or "Ops Hidden") + ", " + \
            (self.client.world.physics and "Physics" or "No Physics") + ", " + \
            (self.client.world.finite_water and "Finite Water" or "Infinite Water")
        )
    
    @op_only
    def commandSetspawn(self, parts):
        "/setspawn - Sets this world's spawn point to the current location."
        x = self.client.x >> 5
        y = self.client.y >> 5
        z = self.client.z >> 5
        h = int(self.client.h*(360/255.0))
        self.client.world.spawn = (x, y, z, h)
        self.client.sendServerMessage("Set spawn point to %s,%s,%s" % (x, y, z))
    
    def commandWhere(self, parts):
        "/where - Returns your current coordinates"
        x = self.client.x >> 5
        y = self.client.y >> 5
        z = self.client.z >> 5
        h = self.client.h
        p = self.client.p
        self.client.sendServerMessage("You are at %s, %s, %s [h%s, p%s]" % (x, y, z, h, p))