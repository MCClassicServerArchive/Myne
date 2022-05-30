
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class PhysicsControlPlugin(ProtocolPlugin):
    
    commands = {
        "physics": "commandPhysics",
        #"physflush": "commandPhysflush",
        "unflood": "commandUnflood",
        "fwater": "commandFwater",
    }
    
    @op_only
    def commandUnflood(self, parts):
        "/unflood worldname - Slowly removes all water and lava from the map."
        self.client.world.start_unflooding()
        self.client.sendWorldMessage("Unflooding has been initiated.")
    
    @admin_only
    @on_off_command
    def commandPhysics(self, onoff):
        "/physics on|off - Enables or disables physics in this world."
        if onoff == "on":
            if self.client.world.physics:
                self.client.sendWorldMessage("Physics is already on here.")
            else:
                if self.client.factory.numberWithPhysics() >= self.client.factory.physics_limit:
                    self.client.sendWorldMessage("There are already %s worlds with physics on (the max)." % self.client.factory.physics_limit)
                else:
                    self.client.world.physics = True
                    self.client.sendWorldMessage("This world now has physics enabled.")
        else:
            if not self.client.world.physics:
                self.client.sendWorldMessage("Physics is already off here.")
            else:
                self.client.world.physics = False
                self.client.sendWorldMessage("This world now has physics disabled.")
    
    @op_only
    @on_off_command
    def commandFwater(self, onoff):
        "/fwater on|off - Enables or disables finite water in this world."
        if onoff == "on":
            self.client.world.finite_water = True
            self.client.sendWorldMessage("This world now has finite water enabled.")
        else:
            self.client.world.finite_water = False
            self.client.sendWorldMessage("This world now has finite water disabled.")
    
    # Needs updating for new physics engine separation
    #@admin_only
    #def commandPhysflush(self,):
    #    "/physflush - Tells the physics engine to rescan the world."
    #    self.client.world.physics_engine.was_physics = False
    #    self.sendServerMessage("Physics flush running.")
    