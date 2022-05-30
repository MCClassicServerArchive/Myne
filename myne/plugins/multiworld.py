
import random
import os

from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class MultiWorldPlugin(ProtocolPlugin):
    
    commands = {
        "new": "commandNew",
        "rename": "commandRename",
        "shutdown": "commandShutdown",
        "load": "commandLoad",
        "join": "commandLoad",
        "l": "commandLoad",
        "boot": "commandBoot",
        "worlds": "commandWorlds",
        "random": "commandRandom",
        "templates": "commandTemplates",
    }
    
    @admin_only
    def commandNew(self, parts):
        "/new worldname [template] - Makes a new world, and boots it."
        if len(parts) == 1:
            self.client.sendServerMessage("Please specify a new world ID.")
        elif self.client.factory.world_exists(parts[1]):
            self.client.sendServerMessage("World ID in use")
        else:
            if len(parts) == 2:
                template = "default"
            else:
                template = parts[2]
            world_id = parts[1].lower()
            self.client.factory.newWorld(world_id, template)
            self.client.factory.loadWorld("worlds/%s" % world_id, world_id)
            self.client.factory.worlds[world_id].all_write = False
            self.client.sendServerMessage("World '%s' made and booted." % world_id)
    
    @admin_only
    def commandRename(self, parts):
        "/rename worldid newworldid - Renames a SHUT DOWN world."
        if len(parts) < 3:
            self.client.sendServerMessage("Please specify two world IDs.")
        else:
            old_worldid = parts[1]
            new_worldid = parts[2]
            if old_worldid in self.client.factory.worlds:
                self.client.sendServerMessage("World '%s' is booted, please shut it down!" % old_worldid)
            elif not self.client.factory.world_exists(old_worldid):
                self.client.sendServerMessage("There is no world '%s'." % old_worldid)
            elif self.client.factory.world_exists(new_worldid):
                self.client.sendServerMessage("There is already a world called '%s'." % new_worldid)
            else:
                self.client.factory.renameWorld(old_worldid, new_worldid)
                self.client.sendServerMessage("World '%s' renamed to '%s'." % (old_worldid, new_worldid))
    
    @admin_only
    def commandShutdown(self, parts):
        "/shutdown worldid - Turns off the named world."
        if len(parts) == 1:
            self.client.sendServerMessage("Please specify a world ID.")
        else:
            if parts[1] in self.client.factory.worlds:
                self.client.factory.unloadWorld(parts[1])
                self.client.sendServerMessage("World '%s' unloaded." % parts[1])
            else:
                self.client.sendServerMessage("World '%s' doesn't exist." % parts[1])
    
    @admin_only
    def commandBoot(self, parts):
        "/boot worldid - Starts up a new world."
        if len(parts) == 1:
            self.client.sendServerMessage("Please specify a world ID.")
        else:
            if parts[1] in self.client.factory.worlds:
                self.client.sendServerMessage("World '%s' already exists!" % parts[1])
            else:
                try:
                    self.client.factory.loadWorld("worlds/%s" % parts[1], parts[1])
                    self.client.sendServerMessage("World '%s' booted." % parts[1])
                except AssertionError:
                    self.client.sendServerMessage("There is no world by that name.")
    
    @only_string_command("world name")
    def commandLoad(self, world_id, params=None):
        "/load worldname - Moves you into world 'worldname'"
        if world_id not in self.client.factory.worlds:
            self.client.sendServerMessage("There's no such world '%s'." % world_id)
        else:
            world = self.client.factory.worlds[world_id]
            if world.private:
                if not self.client.canEnter(world):
                    self.client.sendServerMessage("'%s' is private; you're not allowed in." % world_id)
                    return
            self.client.changeToWorld(world_id)
    
    def commandWorlds(self, parts):
        "/worlds - Lists available worlds"
        self.client.sendServerList(["Available worlds:"] + [id for id, world in self.client.factory.worlds.items() if self.client.canEnter(world)])
    
    def commandTemplates(self, parts):
        "/templates - Lists available templates"
        self.client.sendServerList(["Available templates:"] + os.listdir("templates/"))
    
    def commandRandom(self, parts):
        "/random - Takes you to a random world."
        # Get all public worlds
        target_worlds = list(self.client.factory.publicWorlds())
        # Try excluding us (we may not be public)
        try:
            target_worlds.remove(self.client.world.id)
        except ValueError:
            pass
        # Anything left?
        if not target_worlds:
            self.client.sendServerMessage("There is only one world, and you're in it.")
        else:
            self.client.changeToWorld(random.choice(target_worlds))