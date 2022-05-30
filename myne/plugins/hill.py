
from twisted.internet import reactor

from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

import math

class HillPlugin(ProtocolPlugin):
    
    commands = {
        "hill": "commandHill",
    }
    
    @op_only
    def commandHill(self, parts):
        "/hill - Creates a hill between the two blocks you touched last."
        # Use the last two block places
        try:
            x, y, z = self.client.last_block_changes[0]
            x2, y2, z2 = self.client.last_block_changes[1]
        except IndexError:
            self.client.sendServerMessage("You have not clicked two corners yet.")
            return
        
        if x > x2:
            x, x2 = x2, x
        if y > y2:
            y, y2 = y2, y
        if z > z2:
            z, z2 = z2, z
        
        x_range = x2 - x
        z_range = z2 - z
        
        # Draw all the blocks on, I guess
        # We use a generator so we can slowly release the blocks
        # We also keep world as a local so they can't change worlds and affect the new one
        world = self.client.world
        def generate_changes():
            for i in range(x, x2+1):
                for k in range(z, z2+1):
                    # Work out the height at this place
                    dx = (x_range / 2.0) - abs((x_range / 2.0) - (i - x))
                    dz = (z_range / 2.0) - abs((z_range / 2.0) - (k - z))
                    dy = int((dx**2 * dz**2) ** 0.2)
                    for j in range(y, y+dy+1):
                        block = BLOCK_GRASS if j == y+dy else BLOCK_DIRT
                        try:
                            world[i, j, k] = chr(block)
                        except AssertionError:
                            pass
                        self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                        self.client.sendBlock(i, j, k, block)
                        yield
        
        # Now, set up a loop delayed by the reactor
        block_iter = iter(generate_changes())
        def do_step():
            # Do 10 blocks
            try:
                for x in range(10):
                    block_iter.next()
                reactor.callLater(0.01, do_step)
            except StopIteration:
                pass
        do_step()