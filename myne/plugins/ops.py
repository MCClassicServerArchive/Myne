
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class OpsPlugin(ProtocolPlugin):
    
    commands = {
        "op": "commandOp",
        'deop': "commandDeop",
        "ops": "commandOps",
        "showops": "commandShowops",
        "hideops": "commandHideops",
    }
    
    @op_only
    @username_world_command
    def commandOp(self, username, world):
        "/op username [world] - Adds username to the op list for the world."
        if not self.client.isAdmin() and world != self.client.world:
            self.client.sendServerMessage("You are not an admin!")
            return
        world.ops.add(username)
        self.client.sendServerMessage("Opped %s" % username)
        if username in self.client.factory.usernames:
            user = self.client.factory.usernames[username]
            if user.world == world:
                user.sendOpUpdate()
    
    @op_only
    @username_world_command
    def commandDeop(self, username, world):
        "/deop username [world] - Removes username from the op list for the world."
        if not self.client.isAdmin() and world != self.client.world:
            self.client.sendServerMessage("You are not an admin!")
            return
        try:
            world.ops.remove(username)
        except KeyError:
            self.client.sendServerMessage("%s id not an op." % username)
            return
        self.client.sendServerMessage("Deopped %s" % username)
        if username in self.client.factory.usernames:
            user = self.client.factory.usernames[username]
            if user.world == world:
                user.sendOpUpdate()
    
    def commandOps(self, parts):
        "/ops - Lists this world's ops"
        if not self.client.world.ops:
            self.client.sendServerMessage("This world has no ops.")
        else:
            self.client.sendServerList(["Ops for %s:" % self.client.world.id] + list(self.client.world.ops))
    
    @op_only
    def commandShowops(self, parts):
        "/showops - Highlights admins and ops in this world with colour."
        self.client.world.highlight_ops = True
        self.client.sendServerMessage("%s now has op highlighting." % self.client.world.id)
    
    @op_only
    def commandHideops(self, parts):
        "/hideops - Everyone in the world has the same colour."
        self.client.world.highlight_ops = False
        self.client.sendServerMessage("%s no longer has op highlighting." % self.client.world.id)
