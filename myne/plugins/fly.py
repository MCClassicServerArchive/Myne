
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class FlyPlugin(ProtocolPlugin):
    
    commands = {
        "fly": "commandFly",
        "stand": "commandStand",
    }
    
    hooks = {
        "poschange": "posChanged",
        "newworld": "newWorld",
    }
    
    def gotClient(self):
        self.flying = False
        self.last_flying_block = None
    
    def posChanged(self, x, y, z, h, p):
        "Hook trigger for when the player moves"
        # Are we fake-flying them?
        if self.flying:
            fly_block_loc = ((x>>5),((y+8)>>5)-1,(z>>5))
            if not self.last_flying_block:
                # OK, send the first flying block
                self.client.sendPacked(TYPE_BLOCKSET, fly_block_loc[0], fly_block_loc[1], fly_block_loc[2], BLOCK_STILL_WATER)
            else:
                # Have we moved at all?
                if fly_block_loc != self.last_flying_block:
                    self.client.sendPacked(TYPE_BLOCKSET, self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2], BLOCK_AIR)
                    self.client.sendPacked(TYPE_BLOCKSET, fly_block_loc[0], fly_block_loc[1], fly_block_loc[2], BLOCK_STILL_WATER)
            self.last_flying_block = fly_block_loc
        else:
            if self.last_flying_block:
                self.client.sendPacked(TYPE_BLOCKSET, self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2], BLOCK_AIR)
                self.last_flying_block = None
    
    def newWorld(self, world):
        "Hook to reset portal abilities in new worlds if not op."
        if not self.client.isOp():
            self.flying = False
    
    @admin_only
    @on_off_command
    def commandFly(self, onoff):
        "/fly on|off - Enables or disables bad server-side flying"
        if onoff == "on":
            self.flying = True
            self.client.sendServerMessage("You are now flying")
        else:
            self.flying = False
            self.client.sendServerMessage("You are no longer flying")
    
    @admin_only
    def commandStand(self, params):
        "/stand - Puts a block (which noone else can see) under your feet. For flying."
        self.client.sendPacked(TYPE_BLOCKSET, self.client.x>>5, (self.client.y>>5)-1, (self.client.z>>5), BLOCK_STONE)
    