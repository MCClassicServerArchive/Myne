
import random
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class TreePlugin(ProtocolPlugin):
    
    commands = {
        "tree": "commandTree",
    }
    
    hooks = {
        "blockchange": "blockChanged",
        "newworld": "newWorld",
    }
    
    def gotClient(self):
        self.build_trees = False
        self.trunk_height = 5, 9
        self.fanout = 2, 4
    
    def newWorld(self, world):
        "Hook to reset dynamiting abilities in new worlds if not op."
        if not self.client.isWriter():
            self.build_trees = False
    
    def blockChanged(self, x, y, z, block, selected_block):
        "Hook trigger for block changes."
        tobuild = []
        # Randomise the variables
        trunk_height = random.randint(*self.trunk_height)
        fanout = random.randint(*self.fanout)
        if self.build_trees and block == BLOCK_PLANT:
            # Build the main tree bit
            for i in range(-fanout-1, fanout):
                for j in range(-fanout-1, fanout):
                    for k in range(-fanout-1, fanout):
                        if (i**2 + j**2 + k**2)**0.5 < fanout:
                            tobuild.append((i, j+trunk_height, k, BLOCK_LEAVES))
            # Build the trunk
            for i in range(trunk_height):
                tobuild.append((0, i, 0, BLOCK_LOG))
            # OK, send the build changes
            for dx, dy, dz, block in tobuild:
                try:
                    self.client.world[x+dx, y+dy, z+dz] = chr(block)
                    self.client.sendBlock(x+dx, y+dy, z+dz, block)
                    self.client.factory.queue.put((self.client, TASK_BLOCKSET, (x+dx, y+dy, z+dz, block)))
                except AssertionError:
                    pass
            return True

    @writer_only
    @on_off_command
    def commandTree(self, onoff):
        if onoff == "on":
            self.build_trees = True
            self.client.sendServerMessage("You are now building trees; place a plant!")
        else:
            self.build_trees = False
            self.client.sendServerMessage("You are no longer building trees.")
            

    
    