
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class LockPlugin(ProtocolPlugin):
    
    commands = {
        "lock": "commandLock",
        "unlock": "commandUnlock",
    }
    
    @op_only
    def commandLock(self, parts):
        "/lock - Locks this world from editing except by ops and writers."
        self.client.world.all_write = False
        self.client.sendWorldMessage("This world is now locked.")
        self.client.sendServerMessage("Locked %s" % self.client.world.id)
    
    @op_only
    def commandUnlock(self, parts):
        "/unlock - Unlocks this world so anyone can edit it."
        self.client.world.all_write = True
        self.client.sendWorldMessage("This world is now unlocked.")
        self.client.sendServerMessage("Unlocked %s" % self.client.world.id)
    