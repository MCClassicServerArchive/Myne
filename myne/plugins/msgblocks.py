
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class MsgblockPlugin(ProtocolPlugin):
    
    commands = {
        "msgblock": "commandMsgblock",
        "mb": "commandMsgblock",
        "msgblockend": "commandMsgblockend",
        "mbend": "commandMsgblockend",
        "showmsgblocks": "commandShowmsgblocks",
        "mbshow": "commandShowmsgblocks",
        "msgblockdel": "commandMsgblockdel",
        "mbdel": "commandMsgblockdel",
        "msgblockdelend": "commandMsgblockdelend",
        "mbdelend": "commandMsgblockdelend",
    }
    
    hooks = {
        "blockchange": "blockChanged",
        "poschange": "posChanged",
        "newworld": "newWorld",
    }
    
    def gotClient(self):
        self.msgblock_message = None
        self.msgblock_remove = False
        self.last_block_position = None
    
    def newWorld(self, world):
        "Hook to reset portal abilities in new worlds if not op."
        if not self.client.isOp():
            self.msgblock_message = None
    
    def blockChanged(self, x, y, z, block, selected_block):
        "Hook trigger for block changes."
        if self.client.world.has_message(x, y, z):
            if self.msgblock_remove:
                self.client.world.delete_message(x, y, z)
                self.client.sendServerMessage("You deleted a message block.")
            else:
                self.client.sendServerMessage("That is a message block, you cannot change it. (/mbdel?)")
                return False # False = they weren't allowed to build
        if self.msgblock_message:
            self.client.sendServerMessage("You placed a message block")
            self.client.world.add_message(x, y, z, self.msgblock_message)
    
    def posChanged(self, x, y, z, h, p):
        "Hook trigger for when the player moves"
        rx = x >> 5
        ry = y >> 5
        rz = z >> 5
        # Or a message?
        try:
            if self.client.world.has_message(rx, ry, rz) and (rx, ry, rz) != self.last_block_position:
                self.client._sendMessage(COLOUR_BLUE, self.client.world.get_message(rx, ry, rz))
        except AssertionError:
            pass
        self.last_block_position = (rx, ry, rz)
    
    @op_only
    def commandMsgblock(self, parts):
        "/msgblock message - Makes the next block you place a message block."
        msg_part = (" ".join(parts[1:])).strip()
        if not msg_part:
            self.client.sendServerMessage("Please enter a message.")
            return
        
        new_message = False
        if not self.msgblock_message:
            self.msgblock_message = ""
            self.client.sendServerMessage("You are now placing message blocks.")
            new_message = True
        
        if msg_part[-1] == "\\":
            self.msgblock_message += msg_part[:-1] + " "
        else:
            self.msgblock_message += msg_part + "\n"
        if len(self.msgblock_message) > 200:
            self.msgblock_message = self.msgblock_message[:200]
            self.client.sendServerMessage("Your message ended up longer than 200 chars, and was truncated.")
        elif not new_message:
            self.client.sendServerMessage("Message extended; you've used %i characters." % len(self.msgblock_message))
    
    @op_only
    def commandMsgblockend(self, parts):
        "/msgblockend - Stops placing message blocks."
        self.msgblock_message = None
        self.client.sendServerMessage("You are no longer placing message blocks.")
    
    @op_only
    def commandShowmsgblocks(self, parts):
        "/showmsgblocks - Shows all message blocks as yellow, only to you."
        for offset in self.client.world.messages.keys():
            x, y, z = self.client.world.get_coords(offset)
            self.client.sendPacked(TYPE_BLOCKSET, x, y, z, BLOCK_YELLOW_CLOTH)
        self.client.sendServerMessage("All messages appearing yellow temporarily.")
    
    @op_only
    def commandMsgblockdel(self, parts):
        "/msgblockdel - Enables msgblock-deleting mode"
        self.client.sendServerMessage("You are now able to delete msgblocks. /mbdelend to stop")
        self.msgblock_remove = True
    
    @op_only
    def commandMsgblockdelend(self, parts):
        "/msgblockdelend - Disables msgblock-deleting mode"
        self.client.sendServerMessage("Msgblock deletion mode ended.")
        self.msgblock_remove = False
    