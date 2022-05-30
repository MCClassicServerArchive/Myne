
from myne.plugins import ProtocolPlugin
from myne.decorators import *

class KickBanPlugin(ProtocolPlugin):
    
    commands = {
        "kick": "commandKick",
        "ban": "commandBan",
        "ipban": "commandIpban",
        "unban": "commandUnban",
        "unipban": "commandUnipban",
        "reason": "commandReason",
        "ipreason": "commandIpreason",
    }

    @admin_only
    @username_command
    def commandKick(self, user, params=[]):
        "/kick username - Kicks the user off the server."
        if params:
            user.sendError("Kicked: %s" % " ".join(params))
        else:
            user.sendError("You were kicked.")
    
    @admin_only
    @only_username_command
    def commandBan(self, username, params=[]):
        "/ban username reason - Ban a user from this server."
        if self.client.factory.isBanned(username):
            self.client.sendServerMessage("%s is already banned." % username)
        else:
            if not params:
                self.client.sendServerMessage("Please give a reason.")
            else:
                self.client.factory.addBan(username, " ".join(params))
                if username in self.client.factory.usernames:
                    self.client.factory.usernames[username].sendError("You were banned!")
    
    @admin_only
    @only_username_command
    def commandIpban(self, username, params=[]):
        "/ipban username reason - Ban a user's IP from this server."
        ip = self.client.factory.usernames[username].transport.getPeer().host
        if self.client.factory.isIpBanned(ip):
            self.client.sendServerMessage("IP %s is already banned." % ip)
        else:
            if not params:
                self.client.sendServerMessage("Please give a reason.")
            else:
                self.client.factory.addIpBan(ip, " ".join(params))
                if username in self.client.factory.usernames:
                    self.client.factory.usernames[username].sendError("You were banned!")
    
    @admin_only
    @only_username_command
    def commandUnban(self, username):
        "/unban username - Removes the ban on the user."
        if not self.client.factory.isBanned(username):
            self.client.sendServerMessage("%s is not banned." % username)
        else:
            self.client.factory.removeBan(username)
            self.client.sendServerMessage("%s unbanned." % username)
    
    @admin_only
    @only_string_command("IP")
    def commandUnipban(self, ip):
        "/unipban ip - Removes the ban on the ip."
        if not self.client.factory.isIpBanned(ip):
            self.client.sendServerMessage("%s is not banned." % ip)
        else:
            self.client.factory.removeIpBan(ip)
            self.client.sendServerMessage("%s unbanned." % ip)
    
    @admin_only
    @only_username_command
    def commandReason(self, username):
        "/reason username - Gives the reason a user was banned."
        if not self.client.factory.isBanned(username):
            self.client.sendServerMessage("%s is not banned." % username)
        else:
            self.client.sendServerMessage("Reason: %s" % self.client.factory.banReason(username))
    
    @admin_only
    @only_string_command("IP")
    def commandIpreason(self, ip):
        "/ipreason username - Gives the reason an IP was banned."
        if not self.client.factory.isIpBanned(ip):
            self.client.sendServerMessage("%s is not banned." % ip)
        else:
            self.client.sendServerMessage("Reason: %s" % self.client.factory.ipBanReason(ip))
    