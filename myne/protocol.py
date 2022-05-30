
import struct
import time
import math
import StringIO
import logging
import random
import hashlib
import traceback
import datetime

from twisted.internet.protocol import Protocol
from twisted.internet import reactor

from myne.constants import *
from myne.plugins import protocol_plugins
from myne.decorators import *

class MyneServerProtocol(Protocol):
    
    """
    Main protocol class for communicating with clients.
    Commands are mainly provided by plugins (protocol plugins).
    """
    
    def log(self, message, level=logging.INFO):
        "Fire-and-forget log function which adds in identifying info"
        peer = self.transport.getPeer()
        logging.log(level, "(%s:%s) %s" % (peer.host, peer.port, message))

    def connectionMade(self):
        "We've got a TCP connection, let's set ourselves up."
        
        # We use the buffer because TCP is a stream protocol :)
        self.buffer = ""
        self.loading_world = False
        
        # Load plugins for ourselves
        self.commands = {}
        self.hooks = {}
        self.plugins = [plugin(self) for plugin in protocol_plugins]
        
        # Get an ID for ourselves
        try:
            self.id = self.factory.claimId(self)
        except ServerFull:
            self.sendError("Server is full.")
            return
        
        # Check for IP bans
        ip = self.transport.getPeer().host
        if self.factory.isIpBanned(ip):
            self.sendError("You are banned for: %s" % self.factory.ipBanReason(ip))
            return
        
        self.log("Assigned ID %i" % self.id, level=logging.DEBUG)
        self.factory.joinWorld("default", self)
        self.sent_first_welcome = False
        self.read_only = False
        self.username = None
        self.selected_archive_name = None
        self.initial_position = None
        self.last_block_changes = []
        self.last_block_position = (-1, -1, -1)
    
    def registerCommand(self, command, func):
        "Registers func as the handler for the command named 'command'."
        # Make sure case doesn't matter
        command = command.lower()
        # Warn if already registered
        if command in self.commands:
            self.log("Command '%s' is already registered. Overriding." % command, logging.WARN)
        # Register
        self.commands[command] = func
    
    def unregisterCommand(self, command, func):
        "Unregisters func as command's handler, if it is currently the handler."
        # Make sure case doesn't matter
        command = command.lower()
        try:
            if self.commands[command] == func:
                del self.commands[command]
        except KeyError:
            self.log("Command '%s' is not registered to %s." % (command, func), logging.WARN)
    
    def registerHook(self, hook, func):
        "Registers func as something to be run for hook 'hook'."
        if hook not in self.hooks:
            self.hooks[hook] = []
        self.hooks[hook].append(func)
    
    def unregisterHook(self, hook, func):
        "Unregisters func from hook 'hook'."
        try:
            self.hooks[hook].remove(func)
        except (KeyError, ValueError):
            self.log("Hook '%s' is not registered to %s." % (command, func), logging.WARN)
    
    def unloadPlugin(self, plugin_class):
        "Unloads the given plugin class."
        for plugin in self.plugins:
            if isinstance(plugin, plugin_class):
                self.plugins.remove(plugin)
                plugin.unregister()
    
    def loadPlugin(self, plugin_class):
        self.plugins.append(plugin_class(self))
    
    def runHook(self, hook, *args, **kwds):
        "Runs the hook 'hook'."
        for func in self.hooks.get(hook, []):
            result = func(*args, **kwds)
            # If they return False, we can skip over and return
            if result is not None:
                return result
        return None
    
    def queueTask(self, task, data=[], world=None):
        "Adds the given task to the factory's queue."
        # If they've overridden the world, use that as the client.
        if world:
            self.factory.queue.put((
                world,
                task,
                data,
            ))
        else:
            self.factory.queue.put((
                self,
                task,
                data,
            ))
    
    def sendWorldMessage(self, message):
        "Sends a message to everyone in the current world."
        self.queueTask(TASK_WORLDMESSAGE, (255, self.world, message))
    
    def connectionLost(self, reason):
        
        # Leave the world
        try:
            self.factory.leaveWorld(self.world, self)
        except (KeyError, AttributeError):
            pass
        
        # Remove ourselves from the username list
        if self.username:
            self.factory.recordPresence(self.username)
            try:
                if self.factory.usernames[self.username.lower()] is self:
                    del self.factory.usernames[self.username.lower()]
            except KeyError:
                pass
        
        # Remove from ID list, send removed msgs
        self.factory.releaseId(self.id)
        self.factory.queue.put((self, TASK_PLAYERLEAVE, (self.id,)))
        self.factory.queue.put((self, TASK_ADMINMESSAGE, ("%s disconnected." % self.username,)))
        self.log("Disconnected '%s'" % (self.username,))
        self.log("(reason: %s)" % (reason,), level=logging.DEBUG)
        
        # Kill all plugins
        del self.plugins
        del self.commands
        del self.hooks
        self.connected = 0
    
    def send(self, data):
        self.transport.write(data)
    
    def sendPacked(self, mtype, *args):
        fmt = TYPE_FORMATS[mtype]
        self.transport.write(chr(mtype) + fmt.encode(*args))
    
    def sendError(self, error):
        self.log("Sending error: %s" % error)
        self.sendPacked(TYPE_ERROR, error)
        reactor.callLater(0.2, self.transport.loseConnection)
    
    def duplicateKick(self):
        "Called when someone else logs in with our username"
        self.sendError("You logged in on another computer.")
    
    def packString(self, string, length=64, packWith=" "):
        return string + (packWith*(length-len(string)))

    def isOp(self):
        return (self.username.lower() in self.world.ops) or self.isAdmin()

    def isAdmin(self):
        return self.factory.isAdmin(self.username.lower())
    
    def isWriter(self):
        return (self.username.lower() in self.world.writers) or self.isOp()
    
    def canEnter(self, world):
        if not world.private:
            return True
        else:
            return (self.username.lower() in world.writers) or (self.username.lower() in world.ops) or self.isAdmin()
    
    def dataReceived(self, data):
        # First, add the data we got onto our internal buffer
        self.buffer += data
        # While there's still data there...
        while self.buffer:
            # Examine the first byte, to see what the command is
            type = ord(self.buffer[0])
            format = TYPE_FORMATS[type]
            # See if we have all its data
            if len(self.buffer) - 1 < len(format):
                # Nope, wait a bit
                break
            # OK, decode the data
            parts = list(format.decode(self.buffer[1:]))
            self.buffer = self.buffer[len(format)+1:]
            
            if type == TYPE_INITIAL:
                # Get the client's details
                protocol, self.username, mppass, utype = parts
                # Check their password
                correct_pass = hashlib.md5(self.factory.salt + self.username).hexdigest()[-32:].strip("0")
                mppass = mppass.strip("0")
                if self.factory.verify_names and mppass != correct_pass:
                    self.log("Kicked '%s'; invalid password (%s, %s)" % (self.username, mppass, correct_pass))
                    self.sendError("Incorrect authentication. (try again in 60s?)")
                    return
                self.log("Connected, as '%s'" % self.username)
                # Are they banned?
                if self.factory.isBanned(self.username):
                    self.sendError("You are banned for: %s" % self.factory.banReason(self.username))
                    return
                # OK, see if there's anyone else with that username
                if not self.factory.duplicate_logins and self.username.lower() in self.factory.usernames:
                    self.factory.usernames[self.username.lower()].duplicateKick()
                self.factory.usernames[self.username.lower()] = self
                # Right protocol?
                if protocol != 6:
                    self.sendError("Wrong protocol.")
                    break
                # Send them back our info.
                breakable_admins = self.runHook("canbreakadmin")
                self.sendPacked(
                    TYPE_INITIAL,
                    6, # Protocol version
                    self.packString(self.factory.server_name),
                    self.packString(self.factory.server_message),
                    100 if breakable_admins else 0,
                )
                # Then... stuff
                self.queueTask(TASK_ADMINMESSAGE, ["%s connected." % self.username])
                self.queueTask(TASK_PLAYERCONNECT, [self.id])
                reactor.callLater(0.1, self.sendLevel)
                reactor.callLater(1, self.sendKeepAlive)
            
            elif type == TYPE_BLOCKCHANGE:
                x, y, z, created, block = parts
                
                # If we're read-only, reverse the change
                if not self.world.all_write and not self.isWriter():
                    self.sendBlock(x, y, z)
                    self.sendServerMessage("This map is locked, and you are not a writer.")
                    return
                
                # This try prevents out-of-range errors on the world storage
                try:
                    # Track if we need to send back the block change
                    overridden = False
                    selected_block = block
                    
                    # If we're deleting, block is actually air
                    # (note the selected block is still stored as selected_block)
                    if not created:
                        block = 0
                    
                    # Pre-hook, for stuff like /paint
                    new_block = self.runHook("preblockchange", x, y, z, block, selected_block)
                    if new_block is not None:
                        block = new_block
                        overridden = True
                    
                    # Call hooks
                    new_block = self.runHook("blockchange", x, y, z, block, selected_block)
                    if new_block is False:
                        # They weren't allowed to build here!
                        self.sendBlock(x, y, z)
                        continue
                    elif new_block is True:
                        # Someone else handled building, just continue
                        continue
                    elif new_block is not None:
                        block = new_block
                        overridden = True
                    
                    # OK, save the block
                    self.world[x, y, z] = chr(block)
                    
                    # Now, send the custom block back if we need to
                    if overridden:
                        self.sendBlock(x, y, z, block)
                
                # Out of bounds!
                except (KeyError, AssertionError):
                    self.sendPacked(TYPE_BLOCKSET, x, y, z, "\0")
                
                # OK, replay changes to others
                else:
                    self.factory.queue.put((self, TASK_BLOCKSET, (x, y, z, block)))
                    self.last_block_changes = [(x, y, z)] + self.last_block_changes[:1]
            
            elif type == TYPE_PLAYERPOS:
                # If we're loading a world, ignore these.
                if self.loading_world:
                    continue
                
                naff, x, y, z, h, p = parts
                pos_change = not (x == self.x and y == self.y and z == self.z)
                dir_change = not (h == self.h and p == self.p)
                
                override = self.runHook("poschange", x, y, z, h, p)
                
                # Only send changes if the hook didn't say no
                if override is not False:
                    if pos_change:
                        # Send everything to the other clients
                        self.factory.queue.put((self, TASK_PLAYERPOS, (self.id, self.x, self.y, self.z, self.h, self.p)))
                    elif dir_change:
                        self.factory.queue.put((self, TASK_PLAYERDIR, (self.id, self.h, self.p)))
                
                self.x, self.y, self.z, self.h, self.p = x, y, z, h, p
                
            
            elif type == TYPE_MESSAGE:
                byte, message = parts
                if message.startswith("/"):
                    # It's a command
                    parts = [x.strip() for x in message.split() if x.strip()]
                    command = parts[0].strip("/")
                    
                    # See if we can handle it internally
                    try:
                        func = getattr(self, "command%s" % command.title())
                    except AttributeError:
                        # Can we find it from a plugin?
                        try:
                            func = self.commands[command.lower()]
                        except KeyError:
                            self.sendServerMessage("Unknown command '%s'" % command)
                            return
                    
                    if getattr(func, "admin_only", False) and not self.isAdmin():
                        self.sendServerMessage("'%s' is an admin-only command!" % command)
                        return
                    if getattr(func, "op_only", False) and not self.isOp():
                        self.sendServerMessage("'%s' is an op-only command!" % command)
                        return
                    if getattr(func, "writer_only", False) and not self.isWriter():
                        self.sendServerMessage("'%s' is a writer-only command!" % command)
                        return
                    try:
                        func(parts)
                    except Exception, e:
                        self.sendServerMessage("Internal server error.")
                        self.log(traceback.format_exc(), level=logging.ERROR)
                elif message.startswith(">") or message.startswith("@"):
                    # It's a whisper
                    try:
                        username, text = message[1:].strip().split(" ", 1)
                    except ValueError:
                        self.sendServerMessage("Please include a username and a message to send.")
                    else:
                        username = username.lower()
                        if username in self.factory.usernames:
                            self.factory.usernames[username].sendWhisper(self.username, text)
                            self.sendWhisper(self.username, text)
                        else:
                            self.sendServerMessage("%s is not online." % username)
                else:
                    self.factory.queue.put((self, TASK_MESSAGE, (self.id, self.userColour(), self.username, message)))
            
            else:
                self.log("Unhandleable type %s" % type, logging.WARN)
    
    def userColour(self):
        if self.username.lower() == "notch":
            return COLOUR_YELLOW
        elif self.isAdmin():
            return COLOUR_RED
        elif self.isOp():
            return COLOUR_GREEN
        elif self.isWriter():
            return COLOUR_CYAN
        else:
            return COLOUR_GREY
    
    def colouredUsername(self):
        if self.world.highlight_ops:
            return self.userColour() + self.username
        else:
            return self.username
    
    def teleportTo(self, x, y, z, h=0):
        "Teleports the client to the coordinates"
        if h > 255:
            h = 255
        self.sendPacked(TYPE_PLAYERPOS, 255, (x<<5)+16, (y<<5)+16, (z<<5)+16, h, 0)
    
    def changeToWorld(self, world_id, position=None):
        self.factory.queue.put((self, TASK_WORLDCHANGE, (self.id, self.world)))
        self.loading_world = True
        world = self.factory.joinWorld(world_id, self)
        self.runHook("newworld", world)
        if not self.isOp():
            self.block_overrides = {}
        self.last_block_changes = []
        self.initial_position = position
        if self.world.is_archive:
            self.sendServerMessage("This world is an Archive, and will cease to exist")
            self.sendServerMessage("once the last person leaves.")
        
        breakable_admins = self.runHook("canbreakadmin")
        self.sendPacked(TYPE_INITIAL, 6, "Loading...", "Entering world '%s'" % world_id, 100 if breakable_admins else 0)
        self.sendLevel()
    
    def sendOpUpdate(self):
        "Sends the admincrete-breaker update and a message."
        if self.isOp():
            self.sendServerMessage("You are now an op here.")
        else:
            self.sendServerMessage("You are no longer an op here.")
        self.runHook("rankchange")
        self.respawn()
    
    def sendAdminUpdate(self):
        "Sends the admincrete-breaker update and a message."
        if self.isAdmin():
            self.sendServerMessage("You are now an admin.")
        else:
            self.sendServerMessage("You are no longer an admin.")
        self.runHook("rankchange")
        self.respawn()
    
    def sendWriterUpdate(self):
        "Sends a message."
        if self.isWriter():
            self.sendServerMessage("You are now a writer in this world.")
        else:
            self.sendServerMessage("You are no longer a writer in this world.")
        self.runHook("rankchange")
        self.respawn()
    
    def respawn(self):
        "Respawns the player in-place for other players, updating their nick."
        self.queueTask(TASK_PLAYERRESPAWN, [self.id, self.colouredUsername(), self.x, self.y, self.z, self.h, self.p])
    
    def sendBlock(self, x, y, z, block=None):
        try:
            def real_send(block):
                self.sendPacked(TYPE_BLOCKSET, x, y, z, block)
            if block:
                real_send(block)
            else:
                self.world[x, y, z].addCallback(real_send)
        except AssertionError:
            self.log("Block out of range: %s %s %s" % (x, y, z), level=logging.WARN)
    
    def sendPlayerPos(self, id, x, y, z, h, p):
        self.sendPacked(TYPE_PLAYERPOS, id, x, y, z, h, p)
    
    def sendPlayerDir(self, id, h, p):
        self.sendPacked(TYPE_PLAYERDIR, id, h, p)
    
    def sendMessage(self, id, colour, username, text, direct=False, action=False):
        "Sends a message to the player, splitting it up if needed."
        # See if it's muted.
        replacement = self.runHook("recvmessage", colour, username, text, action)
        if replacement is False:
            return
        # See if we should highlight the names
        if self.world.highlight_ops:
            if action:
                prefix = "* %s%s %s" % (colour, username, COLOUR_WHITE)
            else:
                prefix = "%s%s: %s" % (colour, username, COLOUR_WHITE)
        else:
            if action:
                prefix = "* %s " % username
            else:
                prefix = "%s: " % username
        # Send the message in more than one bit if needed
        self._sendMessage(prefix, text, id)
    
    def _sendMessage(self, prefix, text, id=127):
        "Utility function for sending messages, which does line splitting."
        space_for_text = 64 - len(prefix)
        message_left = text
        while message_left:
            if "\n" in message_left[:space_for_text]:
                segment, message_left = message_left.split("\n", 1)
            else:
                segment = message_left[:space_for_text]
                message_left = message_left[space_for_text:]
            if segment:
                self.sendPacked(TYPE_MESSAGE, id, prefix + segment)
    
    def sendAction(self, id, colour, username, text):
        self.sendMessage(id, colour, username, text, action=True)
    
    def sendWhisper(self, username, text):
        self.sendNormalMessage("%s%s> %s%s" % (COLOUR_PURPLE, username, COLOUR_WHITE, text))
    
    def sendServerMessage(self, message):
        self.sendPacked(TYPE_MESSAGE, 255, message)
    
    def sendNormalMessage(self, message):
        self._sendMessage("", message)
    
    def sendServerList(self, items, wrap_at=63):
        "Sends the items as server messages, wrapping them correctly."
        current_line = items[0]
        for item in items[1:]:
            if len(current_line) + len(item) + 1 > wrap_at:
                self.sendServerMessage(current_line)
                current_line = item
            else:
                current_line += " " + item
        self.sendServerMessage(current_line)
    
    def sendNewPlayer(self, id, username, x, y, z, h, p):
        self.sendPacked(TYPE_SPAWNPOINT, id, username, x, y, z, h, p)
    
    def sendPlayerLeave(self, id,):
        self.sendPacked(TYPE_PLAYERLEAVE, id)
    
    def sendKeepAlive(self):
        if self.connected:
            self.sendPacked(TYPE_KEEPALIVE)
            reactor.callLater(1, self.sendKeepAlive)
    
    def sendOverload(self):
        "Sends an overload - a fake map designed to use as much memory as it can."
        self.sendPacked(TYPE_INITIAL, 6, "Loading...", "Entering world default", 0)
        self.sendPacked(TYPE_PRECHUNK)
        reactor.callLater(0.001, self.sendOverloadChunk)
    
    def sendOverloadChunk(self):
        "Sends a level chunk full of 1s."
        if self.connected:
            self.sendPacked(TYPE_CHUNK, 1024, "\1"*1024, 50)
            reactor.callLater(0.001, self.sendOverloadChunk)
    
    def sendLevel(self):
        "Starts the process of sending a level to the client."
        self.factory.recordPresence(self.username)
        # Ask the World to flush the level and get a gzip handle back to us.
        if hasattr(self, "world"):
            self.world.get_gzip_handle().addCallback(self.sendLevelStart)
    
    def sendLevelStart(self, (gzip_handle, zipped_size)):
        "Called when the world is flushed and the gzip is ready to read."
        # Store that handle and size
        self.zipped_level, self.zipped_size = gzip_handle, zipped_size
        # Preload our first chunk, send a level stream header, and go!
        self.chunk = self.zipped_level.read(1024)
        self.log("Sending level...", level=logging.DEBUG)
        self.sendPacked(TYPE_PRECHUNK)
        reactor.callLater(0.001, self.sendLevelChunk)
    
    def sendLevelChunk(self):
        if not hasattr(self, 'chunk'):
            self.log("Cannot send chunk, there isn't one! %r %r" % (self, self.__dict__), level=logging.ERROR)
            return
        if self.chunk:
            self.sendPacked(TYPE_CHUNK, len(self.chunk), self.chunk, chr(int(100*(self.zipped_level.tell()/float(self.zipped_size)))))
            self.chunk = self.zipped_level.read(1024)
            reactor.callLater(0.001, self.sendLevelChunk)
        else:
            self.zipped_level.close()
            del self.zipped_level
            del self.chunk
            del self.zipped_size
            self.endSendLevel()
        
    def endSendLevel(self):
        self.log("Sent level data", level=logging.DEBUG)
        self.sendPacked(TYPE_LEVELSIZE, self.world.x, self.world.y, self.world.z)
        
        
        sx, sy, sz, sh = self.world.spawn
        self.p = 0
        self.loading_world = False
        
        # If we have a custom point set (teleport, tp), use that
        if self.initial_position:
            try:
                sx, sy, sz, sh = self.initial_position
            except ValueError:
                sx, sy, sz = self.initial_position
                sh = 0
            self.initial_position = None
        
        self.x = (sx<<5)+16
        self.y = (sy<<5)+16
        self.z = (sz<<5)+16
        self.h = int(sh*255/360.0)
        
        self.sendPacked(TYPE_SPAWNPOINT, chr(255), "andrewgodwin", self.x, self.y, self.z, self.h, 0)
        
        self.sendAllNew()
        self.factory.queue.put((self, TASK_NEWPLAYER, (self.id, self.colouredUsername(), self.x, self.y, self.z, self.h, 0)))
        self.sendWelcome()
    
    def sendAllNew(self):
        "Sends a 'new player' notification for each new player in the world."
        for client in self.world.clients:
            if client is not self and hasattr(client, "x"):
                if self.world.highlight_ops:
                    self.sendNewPlayer(client.id, client.userColour() + client.username, client.x, client.y, client.z, client.h, client.p)
                else:
                    self.sendNewPlayer(client.id, client.username, client.x, client.y, client.z, client.h, client.p)
    
    def sendWelcome(self):
        if not self.sent_first_welcome:
            for line in self.factory.initial_greeting.split("\n"):
                self.sendPacked(TYPE_MESSAGE, 127, line.strip())
            self.sent_first_welcome = True
        else:
            self.sendPacked(TYPE_MESSAGE, 255, "You are now in world '%s'" % self.world.id)