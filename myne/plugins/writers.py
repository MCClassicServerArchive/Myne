
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class WritersPlugin(ProtocolPlugin):
    
    commands = {
        "writer": "commandWriter",
        "dewriter": "commandDewriter",
        "writers": "commandWriters",
    }
    
    @op_only
    @username_world_command
    def commandWriter(self, username, world):
        "/writer username [world] - Adds username to the 'writers' list for the world."
        if not self.client.isAdmin() and world != self.client.world:
            self.client.sendServerMessage("You are not an admin!")
            return
        world.writers.add(username)
        self.client.sendServerMessage("Writered %s" % username)
        if username in self.client.factory.usernames:
            user = self.client.factory.usernames[username]
            if user.world == world:
                user.sendWriterUpdate()
    
    @op_only
    @username_world_command
    def commandDewriter(self, username, world):
        "/dewriter username - Removes username from the 'writers' list for the world."
        if not self.client.isAdmin() and world != self.client.world:
            self.client.sendServerMessage("You are not an admin!")
            return
        try:
            world.writers.remove(username)
        except KeyError:
            self.client.sendServerMessage("%s id not a writer." % username)
            return
        self.client.sendServerMessage("Dewritered %s" % username)
        if username in self.client.factory.usernames:
            user = self.client.factory.usernames[username]
            if user.world == world:
                user.sendWriterUpdate()
    
    def commandWriters(self, parts):
        "/writers - Lists this world's writers"
        if not self.client.world.writers:
            self.client.sendServerMessage("This world has no writers.")
        else:
            self.client.sendServerList(["Writers for %s:" % self.client.world.id] + list(self.client.world.writers))
    
