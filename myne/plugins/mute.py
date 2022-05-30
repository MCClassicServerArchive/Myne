
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class MutePlugin(ProtocolPlugin):
    
    commands = {
        "mute": "commandMute",
        "unmute": "commandUnmute",
        "muted": "commandMuted",
    }
    
    hooks = {
        "recvmessage": "messageReceived",
    }
    
    def gotClient(self):
        self.muted = set()
    
    def messageReceived(self, colour, username, text, action):
        "Stop viewing a message if we've muted them."
        if username.lower() in self.muted:
            return False
    
    @only_username_command
    def commandMute(self, username):
        "/mute username - Stops you hearing messages from 'username'."
        self.muted.add(username)
        self.client.sendServerMessage("%s muted." % username)
    
    @only_username_command
    def commandUnmute(self, username):
        "/unmute username - Lets you hear messages from this user again"
        if username in self.muted:
            self.muted.remove(username)
            self.client.sendServerMessage("%s unmuted." % username)
        else:
            self.client.sendServerMessage("%s wasn't muted to start with" % username)
    
    def commandMuted(self, username):
        "/muted - Lists people you have muted."
        if self.muted:
            self.client.sendServerList(["Muted:"] + list(self.muted))
        else:
            self.client.sendServerMessage("You haven't muted anyone.")
    