
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class PortalPlugin(ProtocolPlugin):
    
    commands = {
        "portal": "commandPortal",
        "p": "commandPortal",
        "portalhere": "commandPortalhere",
        "phere": "commandPortalhere",
        "portalend": "commandPortalend",
        "pend": "commandPortalend",
        "clearportals": "commandClearportals",
        "pclear": "commandClearportals",
        "showportals": "commandShowportals",
        "pshow": "commandShowportals",
        "portaldel": "commandPortaldel",
        "pdel": "commandPortaldel",
        "portaldelend": "commandPortaldelend",
        "pdelend": "commandPortaldelend",
        "useportals": "commandUseportals",
        "puse": "commandUseportals",
    }
    
    hooks = {
        "blockchange": "blockChanged",
        "poschange": "posChanged",
        "newworld": "newWorld",
    }
    
    def gotClient(self):
        self.portal_dest = None
        self.portal_remove = False
        self.portals_on = True
        self.last_block_position = None
    
    def blockChanged(self, x, y, z, block, selected_block):
        "Hook trigger for block changes."
        if self.client.world.has_teleport(x, y, z):
            if self.portal_remove:
                self.client.world.delete_teleport(x, y, z)
                self.client.sendServerMessage("You deleted a teleport block.")
            else:
                self.client.sendServerMessage("That is a teleport block, you cannot change it. (/pdel?)")
                return False # False = they weren't allowed to build
        if self.portal_dest:
            self.client.sendServerMessage("You placed a teleport block")
            self.client.world.add_teleport(x, y, z, self.portal_dest)
    
    def posChanged(self, x, y, z, h, p):
        "Hook trigger for when the player moves"
        rx = x >> 5
        ry = y >> 5
        rz = z >> 5
        try:
            world, tx, ty, tz, th = self.client.world.get_teleport(rx, ry, rz)
        except (KeyError, AssertionError):
            pass
        else:
            # Yes there is! do it.
            if self.portals_on:
                try:
                    world = self.client.factory.worlds[world]
                except KeyError:
                    if (rx, ry, rz) != self.last_block_position:
                        self.client.sendServerMessage("'%s' seems to have vanished. Ask an admin (red)." % world)
                else:
                    if not self.client.canEnter(world):
                        if (rx, ry, rz) != self.last_block_position:
                            self.client.sendServerMessage("You're not allowed in '%s' - too bad." % world.id)
                    else:
                        if world == self.client.world:
                            self.client.teleportTo(tx, ty, tz, th)
                        else:
                            self.client.changeToWorld(world.id, position=(tx, ty, tz, th))
        self.last_block_position = (rx, ry, rz)
    
    def newWorld(self, world):
        "Hook to reset portal abilities in new worlds if not op."
        if not self.client.isOp():
            self.portal_dest = None
            self.portal_remove = False
            self.portals_on = True
    
    @op_only
    def commandPortal(self, parts):
        "/portal worldname x y z [r] - Makes the next block you place a portal."
        if len(parts) < 5:
            self.client.sendServerMessage("Please enter a worldname, x, y and z.")
        else:
            try:
                x = int(parts[2])
                y = int(parts[3])
                z = int(parts[4])
            except ValueError:
                self.client.sendServerMessage("x, y and z must be integers")
            else:
                try:
                    h = int(parts[5])
                except IndexError:
                    h = 0
                except ValueError:
                    self.client.sendServerMessage("r must be an integer")
                    return
                if not (0 <= h <= 255):
                    self.client.sendServerMessage("r must be between 0 and 255")
                    return
                self.portal_dest = parts[1], x, y, z, h
                self.client.sendServerMessage("You are now placing portal blocks. /portalend to stop")
    
    @op_only
    def commandPortalhere(self, parts):
        "/portalhere - Enables portal-building mode, to here."
        self.portal_dest = self.client.world.id, self.client.x>>5, self.client.y>>5, self.client.z>>5, self.client.h
        self.client.sendServerMessage("You are now placing portal blocks to here.")
    
    @op_only
    def commandPortalend(self, parts):
        "/portalend - Stops placing portal blocks."
        self.portal_dest = None
        self.portal_remove = False
        self.client.sendServerMessage("You are no longer placing portal blocks.")
    
    @op_only
    def commandClearportals(self, parts):
        "/clearportals - Removes all portals from the map."
        self.client.world.clear_teleports()
        self.client.sendServerMessage("All portals in this world removed.")
    
    @op_only
    def commandShowportals(self, parts):
        "/showportals - Shows all portal blocks as pink, only to you."
        for offset in self.client.world.teleports.keys():
            x, y, z = self.client.world.get_coords(offset)
            self.client.sendPacked(TYPE_BLOCKSET, x, y, z, BLOCK_PINK_CLOTH)
        self.client.sendServerMessage("All portals appearing pink temporarily.")
    
    @op_only
    def commandPortaldel(self, parts):
        "/portaldel - Enables portal-deleting mode"
        self.client.sendServerMessage("You are now able to delete portals. /pdelend to stop")
        self.portal_remove = True
    
    @op_only
    def commandPortaldelend(self, parts):
        "/portaldelend - Disables portal-deleting mode"
        self.client.sendServerMessage("Portal deletion mode ended.")
        self.portal_remove = False
    
    @op_only
    @on_off_command
    def commandUseportals(self, onoff):
        "/useportals on|off - Allows you to enable or diable portal usage."
        if onoff == "on":
            self.portals_on = True
            self.client.sendServerMessage("Portals will now work for you again.")
        else:
            self.portals_on = False
            self.client.sendServerMessage("Portals will now not work for you.")
    