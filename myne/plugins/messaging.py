
import random
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class MessagingPlugin(ProtocolPlugin):
    
    commands = {
        "say": "commandSay",
        "me": "commandMe",
    }
    
    def commandMe(self, parts):
        "/me action - Prints * username action"
        if len(parts) == 1:
            self.client.sendServerMessage("Please type an action.")
        else:
            self.client.factory.queue.put((self.client, TASK_ACTION, (self.client.id, self.client.userColour(), self.client.username, " ".join(parts[1:]))))
    
    @admin_only
    def commandSay(self, parts):
        "/say message - Prints out message in the server colour."
        if len(parts) == 1:
            self.client.sendServerMessage("Please type a message.")
        else:
            self.client.factory.queue.put((self.client, TASK_SERVERMESSAGE, (" ".join(parts[1:]))))
    