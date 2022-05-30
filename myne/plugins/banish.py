
from myne.plugins import ProtocolPlugin
from myne.decorators import *

class BanishPlugin(ProtocolPlugin):
    
    commands = {
        "banish": "commandBanish",
    }
    
    @op_only
    @username_command
    def commandBanish(self, user):
        "/banish username - Banishes the user to the default world."
        if user.world == self.client.world:
            user.sendServerMessage("You were banished from '%s'." % self.client.world.id)
            user.changeToWorld("default")
            self.client.sendServerMessage("User %s banished." % user.username)
        else:
            self.client.sendServerMessage("That user is in another world!")
    