
import random
from myne.plugins import ProtocolPlugin
from myne.decorators import *

class RollPlugin(ProtocolPlugin):
    
    commands = {
        "roll": "commandRoll",
    }
    
    def commandRoll(self, parts):
        "/roll max - Rolls a random number from 1 to max. Announces to world."
        if len(parts) == 1:
            self.client.sendServerMessage("Please enter a number as the maximum roll.")
        else:
            try:
                roll = random.randint(1, int(parts[1]))
            except ValueError:
                self.client.sendServerMessage("Please enter an integer as the maximum roll.")
            else:
                self.client.sendWorldMessage("%s rolled a %s" % (self.client.username, roll))
    