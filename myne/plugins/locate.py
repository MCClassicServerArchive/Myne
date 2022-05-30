
from myne.plugins import ProtocolPlugin
from myne.decorators import *

class LocatePlugin(ProtocolPlugin):
    
    commands = {
        "locate": "commandLocate",
        "find": "commandLocate",
    }

    @username_command
    def commandLocate(self, user):
        "/locate username - Tells you what world a user is in."
        self.client.sendServerMessage("%s is in %s" % (user.username, user.world.id))
    