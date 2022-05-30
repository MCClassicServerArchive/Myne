
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.


"""
An example client. Run simpleserv.py first before running this.
"""

from twisted.internet import reactor, protocol

# a client protocol

class TestClient(protocol.Protocol):
    """Once connected, send a message, then print the result."""
    
    def connectionMade(self):
        print "sending"
        self.transport.write("\0\5andrewgodwin11                                                  16080188f52cd1c25be9075689ccb632                                \0")
    
    def dataReceived(self, data):
        print repr(data)


class Factory(protocol.ClientFactory):
    protocol = TestClient

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed."
        reactor.stop()
    
    def clientConnectionLost(self, connector, reason):
        print "Connection lost."
        reactor.stop()


# this connects the protocol to a server runing on port 8000
def main():
    f = Factory()
    reactor.connectTCP("localhost", 25566, f)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()