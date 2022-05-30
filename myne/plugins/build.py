
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class BuildPlugin(ProtocolPlugin):
    
    commands = {
        "build": "commandBuild",
    }
    
    hooks = {
        "blockchange": "blockChanged",
    }
    
    def gotClient(self):
        self.block_overrides = {}
    
    def blockChanged(self, x, y, z, block, selected_block):
        "Hook trigger for block changes."
        if block in self.block_overrides:
            return self.block_overrides[block]
    
    @writer_only
    def commandBuild(self, parts):
        "/build water|watervator|lava|stilllava|grass|gold|copper|coal"
        possibles = {
            "water": (BLOCK_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
            "watervator": (BLOCK_STILL_WATER, BLOCK_CYAN_CLOTH, "Cyan cloth"),
            "stillwater": (BLOCK_STILL_WATER, BLOCK_CYAN_CLOTH, "Cyan cloth"),
            "lava": (BLOCK_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
            "stilllava": (BLOCK_STILL_LAVA, BLOCK_ORANGE_CLOTH, "Orange cloth"),
            "grass": (BLOCK_GRASS, BLOCK_GREEN_CLOTH, "Green cloth"),
            "coal": (BLOCK_COAL_ORE, BLOCK_DARKGREY_CLOTH, "Dark grey cloth"),
            "gold": (BLOCK_GOLD_ORE, BLOCK_YELLOW_CLOTH, "Yellow cloth"),
            "copper": (BLOCK_COPPER_ORE, BLOCK_TURQUOISE_CLOTH, "Turquoise cloth"),
        }
        if len(parts) == 1:
            self.client.sendServerMessage("Specify a type to toggle.")
        else:
            name = parts[1].lower()
            try:
                new, old, old_name = possibles[name]
            except KeyError:
                self.client.sendServerMessage("'%s' is not a special block type." % name)
            else:
                if old in self.block_overrides:
                    del self.block_overrides[old]
                    self.client.sendServerMessage("%s is back to normal." % old_name)
                else:
                    self.block_overrides[old] = new
                    self.client.sendServerMessage("%s will turn into %s." % (old_name, name))
    
    