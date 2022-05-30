
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class AdminsPlugin(ProtocolPlugin):
    
    commands = {
        "admin": "commandAdmin",
        "deadmin": "commandDeadmin",
    }

    @admin_only
    @only_username_command
    def commandAdmin(self, username):
        "/admin username - Adds the user as an admin."
        self.client.factory.admins.add(username)
        self.client.sendServerMessage("%s is now an admin." % username)
        if username in self.client.factory.usernames:
            self.client.factory.usernames[username].sendAdminUpdate()

    @admin_only
    @only_username_command
    def commandDeadmin(self, username):
        "/deadmin username - Removes the user as an admin."
        self.client.factory.admins.remove(username)
        self.client.sendServerMessage("%s is no longer an admin." % username.lower())
        if username in self.client.factory.usernames:
            self.client.factory.usernames[username].sendAdminUpdate()
    