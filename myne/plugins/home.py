
import random
from myne.plugins import ProtocolPlugin
from myne.decorators import *

class HomePlugin(ProtocolPlugin):
    
    commands = {
        "home": "commandHome",
    }
    
    def commandHome(self, parts):
        "/home - Takes you back to the portal world."
        self.client.changeToWorld("portal")
    