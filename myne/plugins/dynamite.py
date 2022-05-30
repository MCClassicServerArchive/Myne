
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *
from twisted.internet import reactor

class DynamitePlugin(ProtocolPlugin):
    
    commands = {
        "dynamite": "commandDynamite",
    }
    
    hooks = {
        "blockchange": "blockChanged",
        "newworld": "newWorld",
    }
    
    def gotClient(self):
        self.build_dynamite = False
        self.explosion_radius = 2
        self.delay = 2
    
    def newWorld(self, world):
        "Hook to reset dynamiting abilities in new worlds if not op."
        if not self.client.isOp():
            self.build_dynamite = False
    
    def blockChanged(self, x, y, z, block, selected_block):
        "Hook trigger for block changes."
        tobuild = []
        # Randomise the variables
        fanout = self.explosion_radius
        if self.build_dynamite and block == BLOCK_WOOD:
            def explode():
                # Clear the explosion radius
                for i in range(-fanout, fanout+1):
                    for j in range(-fanout, fanout+1):
                        for k in range(-fanout, fanout+1):
                                tobuild.append((i, j, k, BLOCK_AIR))
                # OK, send the build changes
                for dx, dy, dz, block in tobuild:
                    try:
                        self.client.world[x+dx, y+dy, z+dz] = chr(block)
                        self.client.sendBlock(x+dx, y+dy, z+dz, block)
                        self.client.factory.queue.put((self.client, TASK_BLOCKSET, (x+dx, y+dy, z+dz, block)))
                    except AssertionError: # OOB
                        pass
            # Explode in 2 seconds
            reactor.callLater(self.delay, explode)

    @op_only
    @on_off_command
    def commandDynamite(self, onoff):
        if onoff == "on":
            self.build_dynamite = True
            self.client.sendServerMessage("You are now building dynamite; place a wood block!")
        else:
            self.build_dynamite = False
            self.client.sendServerMessage("You are no longer building dynamite.")
            

    
    