
import time

from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class PlayersPlugin(ProtocolPlugin):
    
    commands = {
        "who": "commandWho",
        "lastseen": "commandLastseen",
    }
    
    @admin_only
    @only_username_command
    def commandLastseen(self, username):
        "/lastseen username - Tells you when 'username' was last seen."
        if username not in self.client.factory.lastseen:
            self.client.sendServerMessage("There are no records of %s." % username)
        else:
            t = time.time() - self.client.factory.lastseen[username]
            days = t // 86400
            hours = (t % 86400) // 3600
            mins = (t % 3600) // 60
            desc = "%id, %ih, %im" % (days, hours, mins)
            self.client.sendServerMessage("%s: last seen %s ago." % (username, desc))
    
    def commandWho(self, parts):
        "/who - Shows who is on the server."
        self.client.sendServerList(["Users:"] + list(self.client.factory.usernames))