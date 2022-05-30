
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class PaintPlugin(ProtocolPlugin):
    
    commands = {
        "paint": "commandPaint",
    }
    
    hooks = {
        "preblockchange": "blockChanged",
    }
    
    def gotClient(self):
        self.painting = False
    
    def blockChanged(self, x, y, z, block, selected_block):
        "Hook trigger for block changes."
        if block is BLOCK_AIR and self.painting:
            return selected_block
    
    def commandPaint(self, parts):
        "/paint - Lets you break-and-build in one move. Toggle."
        if self.painting:
            self.painting = False
            self.client.sendServerMessage("Painting mode is now off.")
        else:
            self.painting = True
            self.client.sendServerMessage("Painting mode is now on.")
    
    