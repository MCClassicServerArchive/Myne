
import sys
import os
import fcntl
import datetime
import struct
from ConfigParser import SafeConfigParser as ConfigParser
import urllib
import urllib2
import cookielib
import re

from twisted.internet import reactor, protocol

from protocol import MyneServerProtocol, TYPE_FORMATS
from constants import *

# Set stdin to nonblocking
fcntl.fcntl(0, fcntl.F_SETFL, os.O_NONBLOCK)

COLOR_CHARS = ["&%s" % c for c in "0123456789abcdef"]

class ChatClient(MyneServerProtocol):
    """Once connected, allows chatting, but no movement."""
    
    def connectionMade(self):
        print "Identifying to server..."
        self.buffer = ""
        self.chat_buffer = ""
        self.name = None
        self.gzipped = ""
        self.sendPacked(TYPE_INITIAL, 6, self.factory.username, self.factory.mppass, 0)
        reactor.callLater(0.1, self.checkStdin)
    
    def checkStdin(self):
        "Reads stdin, possibly sending a message."
        try:
            data = sys.stdin.read()
        except IOError:
            data = None
        if data:
            self.chat_buffer += data
            lines = self.chat_buffer.split("\n")
            print
            for line in lines[:-1]:
                self.sendPacked(TYPE_MESSAGE, 255, line[:64])
            self.chat_buffer = lines[-1]
        reactor.callLater(0.1, self.checkStdin)
    
    def connectionLost(self, reason):
        pass
    
    def dataReceived(self, data):
        # First, add the data we got onto our internal buffer
        self.buffer += data
        # While there's still data there...
        while self.buffer:
            # Examine the first byte, to see what the command is
            type = ord(self.buffer[0])
            try:
                format = TYPE_FORMATS[type]
            except KeyError:
                self.transport.loseConnection()
            # See if we have all its data
            if len(self.buffer) - 1 < len(format):
                # Nope, wait a bit
                break
            # OK, decode the data
            try:
                parts = list(format.decode(self.buffer[1:]))
            except Exception, e:
                print "%s! string: %r" % (e, self.buffer)
                self.buffer = ""
                continue
            self.buffer = self.buffer[len(format)+1:]
            if type == TYPE_MESSAGE:
                if parts[0] == 255:
                    print "> %s" % parts[1]
                else:
                    msg = parts[1]
                    for colour in COLOR_CHARS:
                        msg = msg.replace(colour, "")
                    print msg
            elif type == TYPE_ERROR:
                print "Error! %s" % parts[0]
                self.transport.loseConnection()


class ChatFactory(protocol.ClientFactory):
    protocol = ChatClient
    
    def __init__(self, username, mppass):
        self.username = username
        self.mppass = mppass

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed."
        reactor.stop()
    
    def clientConnectionLost(self, connector, reason):
        print "Connection terminated."
        reactor.stop()


# this connects the protocol to a server runing on port 8000
def rip(key, username, password):
    login_url = 'http://minecraft.net/login.jsp'
    play_url = 'http://minecraft.net/play.jsp?server=%s'
    
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    login_data = urllib.urlencode({'username': username, 'password': password})
    print "Logging in..."
    opener.open(login_url, login_data)
    print "Fetching server info..."
    html = opener.open(play_url % key).read()
    ip = re.search(r'param name\="server" value="([0-9.]+)"', html).groups()[0]
    port = int(re.search(r'param name\="port" value="([0-9]+)"', html).groups()[0])
    mppass = re.search(r'param name\="mppass" value="([0-9a-zA-Z]+)"', html).groups()[0]
    print "Got details. Connecting..."
    f = ChatFactory(username, mppass)
    reactor.connectTCP(ip, port, f)
    reactor.run()

def main():
    config = ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), "client.conf"))
    rip(sys.argv[1], config.get("client", "username"), config.get("client", "password"))

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()