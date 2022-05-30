
import logging
import traceback
import simplejson

from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory

class ControllerProtocol(LineReceiver):
    
    """
    Protocol for dealing with controller requests.
    """
    
    def connectionMade(self):
        peer = self.transport.getPeer()
        logging.log(logging.INFO, "Control connection made from %s:%s" % (peer.host, peer.port))
        self.factory, self.controller_factory = self.factory.main_factory, self.factory
    
    def connectionLost(self, reason):
        peer = self.transport.getPeer()
        logging.log(logging.INFO, "Control connection lost from %s:%s" % (peer.host, peer.port))
    
    def sendJson(self, data):
        self.sendLine(simplejson.dumps(data))
    
    def lineReceived(self, line):
        data = simplejson.loads(line)
        peer = self.transport.getPeer()
        if data['password'] != self.factory.control_password:
            self.sendJson({"error": "invalid password"})
            logging.log(logging.INFO, "Control: Invalid password %s (%s:%s)" % (data, peer.host, peer.port))
        else:
            command = data['command'].lower()
            try:
                func = getattr(self, "command%s" % command.title())
            except AttributeError:
                self.sendLine("ERROR Unknown command '%s'" % command)
            else:
                logging.log(logging.INFO, "Control: %s %s (%s:%s)" % (command.upper(), data, peer.host, peer.port))
                try:
                    func(data)
                except Exception, e:
                    self.sendLine("ERROR %s" % e)
                    traceback.print_exc()
    
    def commandUsers(self, data):
        self.sendJson({"users": list(self.factory.usernames.keys())})
        
    def commandAdmins(self, data):
        self.sendJson({"admins": list(self.factory.admins)})
    
    def commandWorlds(self, data):
        self.sendJson({"worlds": list(self.factory.worlds.keys())})
    
    def commandUserworlds(self, data):
        self.sendJson({"worlds": [
            (world.id, [client.username for client in world.clients if client.username], {
                "id": world.id,
                "ops": list(world.ops),
                "writers": list(world.writers),
                "private": world.private,
                "archive": world.is_archive,
                "locked": not world.all_write,
                "physics": world.physics,
            })
            for world in self.factory.worlds.values()
        ]})
    
    def commandWorldinfo(self, data):
        world = self.factory.worlds[data['world_id']]
        self.sendJson({
            "id": world.id,
            "ops": list(world.ops),
            "writers": list(world.writers),
            "private": world.private,
            "archive": world.is_archive,
            "locked": not world.all_write,
            "physics": world.physics,
        })


class ControllerFactory(Factory):
    
    protocol = ControllerProtocol
    
    def __init__(self, main_factory):
        self.main_factory = main_factory