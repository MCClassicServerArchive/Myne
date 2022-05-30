
from myne.plugins import ProtocolPlugin
from myne.decorators import *


class DebugPlugin(ProtocolPlugin):
    
    commands = {
        "sanal": "commandStartanalysis",
        "eanal": "commandEndanalysis",
        "test": "commandTest",
    }
    
    def gotClient(self):
        from guppy import hpy
        self.h = hpy()
    
    def commandStartanalysis(self, user):
        self.h.setrelheap()
    
    def commandEndanalysis(self, user):
        hp = self.h.heap()
        import pdb
        pdb.set_trace()
    
    def commandTest(self, parts):
        import logging
        logging.log(logging.ERROR, "Test error!")
    
    def __del__(self):
        print "delDebug"

print "IMPORTED DEBUG PLUGIN"
    
    