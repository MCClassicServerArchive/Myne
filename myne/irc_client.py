
from twisted.words.protocols import irc
from twisted.internet import protocol

import logging
from constants import *

class ChatBot(irc.IRCClient):
    """An IRC-server chat integration bot."""
    
    nickname = "arbot"
    
    def connectionMade(self):
        self.nickname = self.factory.main_factory.irc_nick
        irc.IRCClient.connectionMade(self)
        self.factory.instance = self
        self.factory, self.controller_factory = self.factory.main_factory, self.factory
        logging.log(logging.INFO, "IRC client connected.")
        self.world = None

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        logging.log(logging.INFO, "IRC client disconnected. (%s)" % reason)

    # callbacks for events

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.irc_channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        logging.log(logging.INFO, "IRC client joined %s." % channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        msg = "".join([char for char in msg if ord(char) < 128 and char != "&"])
        
        if channel == self.factory.irc_channel:
            if msg.startswith(self.nickname):
                self.factory.queue.put((self, TASK_MESSAGE, (127, COLOUR_PURPLE, user, msg[len(self.nickname):].strip(":").strip())))

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        msg = "".join([char for char in msg if ord(char) < 128 and char != "&"])
        self.factory.queue.put((self, TASK_ACTION, (127, COLOUR_PURPLE, user, msg)))

    def sendMessage(self, username, message):
        self.msg(self.factory.irc_channel, "%s: %s" % (username, message))

    def sendServerMessage(self, message):
        self.msg(self.factory.irc_channel, ">> %s" % (message, ))

    def sendAction(self, username, message):
        self.msg(self.factory.irc_channel, "* %s %s" % (username, message))

    # irc callbacks

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        pass


class ChatBotFactory(protocol.ClientFactory):

    # the class of the protocol to build when new connection is made
    protocol = ChatBot
    
    def __init__(self, main_factory):
        self.main_factory = main_factory
        self.instance = None

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        self.instance = None
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        logging.log(logging.WARN, "IRC connection failed: %s" % reason)
        self.instance = None

    def sendMessage(self, username, message):
        if self.instance:
            self.instance.sendMessage(username, message)

    def sendAction(self, username, message):
        if self.instance:
            self.instance.sendAction(username, message)

    def sendServerMessage(self, message):
        if self.instance:
            self.instance.sendServerMessage(message)
