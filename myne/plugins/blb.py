
from twisted.internet import reactor

from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class BlbPlugin(ProtocolPlugin):
    
    commands = {
        "blb": "commandBlb",
    }
    
    @op_only
    def commandBlb(self, parts):
        "/blb type [x y z x2 y2 z2] - Sets all blocks in this cuboid to type."
        if len(parts) < 8 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a type (and possibly two coord triples)")
        else:
            # Try getting the block as a direct integer type.
            try:
                block = chr(int(parts[1]))
            except ValueError:
                # OK, try a symbolic type.
                try:
                    block = chr(globals()['BLOCK_%s' % parts[1].upper()])
                except KeyError:
                    self.client.sendServerMessage("'%s' is not a valid block type." % parts[1])
                    return
            
            # Check the block is valid
            if ord(block) > 41:
                self.client.sendServerMessage("'%s' is not a valid block type." % parts[1])
                return
            
            # If they only provided the type argument, use the last two block places
            if len(parts) == 2:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All parameters must be integers")
                    return
            
            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z
            
            if self.client.isAdmin():
                limit = 300000
            else:
                limit = 50000
            # Stop them doing silly things
            if (x2 - x) * (y2 - y) * (z2 - z) > limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to blb.")
                return
            
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for i in range(x, x2+1):
                    for j in range(y, y2+1):
                        for k in range(z, z2+1):
                            try:
                                world[i, j, k] = block
                            except AssertionError:
                                self.client.sendServerMessage("Out of bounds blb error.")
                                return
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