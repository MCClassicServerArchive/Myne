import urllib
import time
import logging
import os
import re
import sys
import datetime
import shutil
import traceback

from Queue import Queue, Empty
from twisted.internet.protocol import Factory
from twisted.internet import reactor
from ConfigParser import RawConfigParser as ConfigParser

from myne.protocol import MyneServerProtocol
from myne.world import World
from myne.irc_client import ChatBotFactory
from myne.constants import *
from myne.plugins import *


class Heartbeat(object):
    """
    Deals with registering with the Minecraft main server every so often.
    The Salt is also used to help verify users' identities.
    """
    
    def __init__(self, factory):
        self.factory = factory
        self.get_url()
    
    def get_url(self):
        try:
            fh = urllib.urlopen("http://www.minecraft.net/heartbeat.jsp", urllib.urlencode({
                "port": self.factory.config.getint("network", "port"),
                "users": len(self.factory.clients),
                "max": self.factory.max_clients,
                "name": self.factory.server_name,
                "public": self.factory.public,
                "version": 6,
                "salt": self.factory.salt,
            }))
            self.url = fh.read().strip()
            logging.log(logging.INFO, "Heartbeat sent. URL: %s" % self.url)
        finally:
            reactor.callLater(45, self.get_url)


class MyneFactory(Factory):
    
    """
    Factory that deals with the general world actions and cross-player comms.
    """
    
    protocol = MyneServerProtocol
    
    def __init__(self):
        self.config = ConfigParser()
        self.config.read("server.conf")
        
        self.max_clients = self.config.getint("server", "max_clients")
        self.server_name = self.config.get("server", "name")
        self.server_message = self.config.get("server", "description")
        self.initial_greeting = self.config.get("server", "greeting").replace("\\n", "\n")
        self.public = self.config.getboolean("server", "public")
        self.duplicate_logins = self.config.getboolean("server", "duplicate_logins")
        self.verify_names = self.config.getboolean("server", "verify_names")
        self.control_password = self.config.get("server", "control_password")
        self.physics_limit = self.config.getint("server", "physics_limit")
        self.info_url = self.config.get("server", "info_url")
        
        # Parse IRC section
        if self.config.has_section("irc"):
            self.irc_nick = self.config.get("irc", "nick")
            self.irc_channel = self.config.get("irc", "channel")
            self.irc_relay = ChatBotFactory(self)
            reactor.connectTCP(self.config.get("irc", "server"), self.config.getint("irc", "port"), self.irc_relay)
        else:
            self.irc_relay = None
        
        # Salt, for the heartbeat server/verify-names
        self.salt = "mysalt%s" % time.time()
        
        # Load up the plugins specified
        plugins = self.config.options("plugins")
        logging.log(logging.INFO, "Loading plugins...")
        load_plugins(plugins)
        
        # Open the chat log, ready for appending
        self.chatlog = open("chatlog.log", "a")
        
        # Create a default world, if there isn't one.
        if not os.path.isdir("worlds/default"):
            logging.log(logging.INFO, "Generating default world...")
            sx, sy, sz = 256, 64, 256
            grass_to = (sy // 2)
            world = World.create(
                "worlds/default",
                sx, sy, sz, # Size
                sx//2,grass_to+2, sz//2, 0, # Spawn
                ([BLOCK_DIRT]*(grass_to-1) + [BLOCK_GRASS] + [BLOCK_AIR]*(sy-grass_to)) # Levels
            )
            logging.log(logging.INFO, "Generated.")
        
        # Initialise internal datastructures
        self.worlds = {}
        self.admins = set()
        self.banned = {}
        self.ipbanned = {}
        self.lastseen = {}
        
        # Load up the contents of those.
        self.loadMeta()
        
        # Set up a few more things.
        self.queue = Queue()
        self.clients = {}
        self.usernames = {}
        self.heartbeat = Heartbeat(self)
        
        # Boot worlds that got loaded
        for world in self.worlds:
            self.loadWorld("worlds/%s" % world, world)
        
        # Set up tasks to run during execution
        reactor.callLater(0.1, self.sendMessages)
        reactor.callLater(30, self.printInfo)
        reactor.callLater(1, self.loadArchives)
        self.world_save_stack = []
        reactor.callLater(60, self.saveWorlds)
    
    
    def loadMeta(self):
        "Loads the 'meta' - variables that change with the server (worlds, admins, etc.)"
        
        config = ConfigParser()
        config.read("server.meta")
        
        # Read in the worlds
        if config.has_section("worlds"):
            for name in config.options("worlds"):
                self.worlds[name] = None
        else:
            self.worlds['default'] = None
        
        # Read in the admins
        if config.has_section("admins"):
            for name in config.options("admins"):
                self.admins.add(name)
        
        # Read in the bans
        if config.has_section("banned"):
            for name in config.options("banned"):
                self.banned[name] = config.get("banned", name)
        
        # Read in the ipbans
        if config.has_section("ipbanned"):
            for ip in config.options("ipbanned"):
                self.ipbanned[ip] = config.get("ipbanned", ip)
        
        # Read in the lastseen
        if config.has_section("lastseen"):
            for username in config.options("lastseen"):
                self.lastseen[username] = config.getfloat("lastseen", username)
    
    
    def saveMeta(self):
        "Saves the server's meta back to a file."
        config = ConfigParser()
        
        # Make the sections
        config.add_section("worlds")
        config.add_section("admins")
        config.add_section("banned")
        config.add_section("ipbanned")
        config.add_section("lastseen")
        
        # Write out things
        for world in self.worlds:
            config.set("worlds", world, "true")
        for admin in self.admins:
            config.set("admins", admin, "true")
        for ban, reason in self.banned.items():
            config.set("banned", ban, reason)
        for ipban, reason in self.ipbanned.items():
            config.set("ipbanned", ipban, reason)
        for username, ls in self.lastseen.items():
            config.set("lastseen", username, str(ls))
        
        fp = open("server.meta", "w")
        config.write(fp)
        fp.close()
    
    def printInfo(self):
        logging.log(logging.INFO, "There are %s users on the server" % len(self.clients))
        #for key in self.worlds:
        #    logging.log(logging.INFO, "%s: %s" % (key, ", ".join(str(c.username) for c in self.worlds[key].clients)))
        reactor.callLater(60, self.printInfo)
    
    def saveWorlds(self):
        "Saves the worlds, one at a time, with a 1 second delay."
        if not self.world_save_stack:
            self.world_save_stack = list(self.worlds)
        
        key = self.world_save_stack.pop()
        self.saveWorld(key)
        
        if not self.world_save_stack:
            reactor.callLater(60, self.saveWorlds)
            self.saveMeta()
        else:
            reactor.callLater(1, self.saveWorlds)
    
    def saveWorld(self, world_id):
        world = self.worlds[world_id]
        world.save_meta()
        world.flush()
    
    def claimId(self, client):
        for i in range(1, self.max_clients+1):
            if i not in self.clients:
                self.clients[i] = client
                return i
        raise ServerFull
    
    def releaseId(self, id):
        del self.clients[id]
    
    def joinWorld(self, worldid, user):
        "Makes the player join the given World."
        new_world = self.worlds[worldid]
        if hasattr(user, "world") and user.world:
            self.leaveWorld(user.world, user)
        user.world = new_world
        new_world.clients.add(user)
        return new_world
    
    def leaveWorld(self, world, user):
        world.clients.remove(user)
        if world.is_archive and not world.clients:
            self.unloadWorld(world.id)
    
    def loadWorld(self, filename, world_id):
        """
        Loads the given world file under the given world ID, or a random one.
        Returns the ID of the new world.
        """
        world = self.worlds[world_id] =  World(filename)
        world.source = filename
        world.clients = set()
        world.id = world_id
        world.factory = self
        world.start()
        logging.log(logging.INFO, "World '%s' booted." % world_id)
        return world_id
    
    def unloadWorld(self, world_id):
        """
        Unloads the given world ID.
        """
        assert world_id != "default"
        for client in list(list(self.worlds[world_id].clients))[:]:
            client.changeToWorld("default")
            client.sendServerMessage("World '%s' has been shut down." % world_id)
        self.worlds[world_id].stop()
        self.worlds[world_id].flush()
        self.worlds[world_id].save_meta()
        del self.worlds[world_id]
        logging.log(logging.INFO, "World '%s' shut down." % world_id)
    
    def publicWorlds(self):
        """
        Returns the IDs of all public worlds
        """
        for world_id, world in self.worlds.items():
            if not world.private:
                yield world_id
    
    def recordPresence(self, username):
        """
        Records a sighting of 'username' in the lastseen dict.
        """
        self.lastseen[username.lower()] = time.time()
    
    def unloadPlugin(self, plugin_name):
        "Reloads the plugin with the given module name."
        # Unload the plugin from everywhere
        for plugin in plugins_by_module_name(plugin_name):
            if issubclass(plugin, ProtocolPlugin):
                for client in self.clients.values():
                    client.unloadPlugin(plugin)
        # Unload it
        unload_plugin(plugin_name)
    
    def loadPlugin(self, plugin_name):
        # Load it
        load_plugin(plugin_name)
        # Load it back into clients etc.
        for plugin in plugins_by_module_name(plugin_name):
            if issubclass(plugin, ProtocolPlugin):
                for client in self.clients.values():
                    client.loadPlugin(plugin)
    
    def sendMessages(self):
        "Sends all queued messages, and lets worlds recieve theirs."
        try:
            while True:
                # Get the next task
                source_client, task, data = self.queue.get_nowait()
                
                try:
                    if isinstance(source_client, World):
                        world = source_client
                    else:
                        try:
                            world = source_client.world
                        except AttributeError:
                            logging.log(logging.WARN, "Source client for message has no world. Ignoring.")
                            continue
                
                    # Someone built/deleted a block
                    if task is TASK_BLOCKSET:
                        # Only run it for clients who weren't the source.
                        for client in world.clients:
                            if client != source_client:
                                client.sendBlock(*data)
                    # Someone moved
                    elif task is TASK_PLAYERPOS:
                        # Only run it for clients who weren't the source.
                        for client in world.clients:
                            if client != source_client:
                                client.sendPlayerPos(*data)
                    # Someone moved only their direction
                    elif task is TASK_PLAYERDIR:
                        # Only run it for clients who weren't the source.
                        for client in world.clients:
                            if client != source_client:
                                client.sendPlayerDir(*data)
                    # Someone spoke!
                    elif task is TASK_MESSAGE:
                        for client in self.clients.values():
                            client.sendMessage(*data)
                        id, colour, username, text = data
                        logging.log(logging.INFO, "%s: %s" % (username, text))
                        self.chatlog.write("%s %s: %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M"), username, text))
                        self.chatlog.flush()
                        if self.irc_relay and world:
                            self.irc_relay.sendMessage(username, text)
                    # Someone actioned!
                    elif task is TASK_ACTION:
                        for client in self.clients.values():
                            client.sendAction(*data)
                        id, colour, username, text = data
                        logging.log(logging.INFO, "* %s %s" % (username, text))
                        self.chatlog.write("%s * %s %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M"), username, text))
                        self.chatlog.flush()
                        if self.irc_relay and world:
                            self.irc_relay.sendAction(username, text)
                    # Someone connected to the server
                    elif task is TASK_PLAYERCONNECT:
                        if self.irc_relay and world:
                            self.irc_relay.sendServerMessage("%s has connected." % source_client.username)
                    # Someone joined a world!
                    elif task is TASK_NEWPLAYER:
                        for client in world.clients:
                            if client != source_client:
                                client.sendNewPlayer(*data)
                            client.sendServerMessage("%s has appeared." % source_client.username)
                    # Someone left!
                    elif task is TASK_PLAYERLEAVE:
                        # Only run it for clients who weren't the source.
                        for client in world.clients:
                            client.sendPlayerLeave(*data)
                            client.sendServerMessage("%s has disconnected." % source_client.username)
                        if self.irc_relay and world:
                            self.irc_relay.sendServerMessage("%s has disconnected." % source_client.username)
                    # Someone changed worlds!
                    elif task is TASK_WORLDCHANGE:
                        # Only run it for clients who weren't the source.
                        for client in data[1].clients:
                            client.sendPlayerLeave(data[0])
                            client.sendServerMessage("%s left for '%s'" % (source_client.username, world.id))
                        logging.log(logging.INFO, "%s is now in '%s'" % (source_client.username, world.id))
                    elif task == TASK_ADMINMESSAGE:
                        # Give all admins the message
                        for username, client in self.usernames.items():
                            if self.isAdmin(username):
                                client.sendServerMessage(data[0])
                    elif task == TASK_WORLDMESSAGE:
                        # Give all world people the message
                        id, world, message = data
                        for client in world.clients:
                            client.sendServerMessage(message)
                    elif task == TASK_SERVERMESSAGE:
                        # Give all people the message
                        message = data
                        for client in self.clients.values():
                            client.sendNormalMessage(COLOUR_PURPLE + message)
                        if self.irc_relay and world:
                            self.irc_relay.sendServerMessage(message)
                    elif task == TASK_PLAYERRESPAWN:
                        # We need to immediately respawn the player to update their nick.
                        for client in world.clients:
                            if client != source_client:
                                id, username, x, y, z, h, p = data
                                client.sendPlayerLeave(id)
                                client.sendNewPlayer(id, username, x, y, z, h, p)
                except Exception, e:
                    logging.log(logging.ERROR, traceback.format_exc())
        except Empty:
            pass
        # OK, now, for every world, let them read their queues
        for world in self.worlds.values():
            world.read_queue()
        # Come back soon!
        reactor.callLater(0.1, self.sendMessages)
    
    def newWorld(self, new_name, template="default"):
        "Creates a new world from some template."
        # Make the directory
        os.mkdir("worlds/%s" % new_name)
        # Find the template files, copy them to the new location
        for filename in ["blocks.gz", "world.meta"]:
            shutil.copyfile("templates/%s/%s" % (template, filename), "worlds/%s/%s" % (new_name, filename))
    
    def renameWorld(self, old_worldid, new_worldid):
        "Renames a world."
        assert old_worldid not in self.worlds
        assert self.world_exists(old_worldid)
        assert not self.world_exists(new_worldid)
        os.rename("worlds/%s" % (old_worldid), "worlds/%s" % (new_worldid))
    
    def loadArchive(self, filename):
        "Boots an archive given a filename. Returns the new world ID."
        # Get an unused world name
        i = 1
        while self.world_exists("a-%i" % i):
            i += 1
        world_id = "a-%i" % i
        # Copy and boot
        self.newWorld(world_id, "../archives/%s" % filename)
        self.loadWorld("worlds/%s" % world_id, world_id)
        world = self.worlds[world_id]
        world.is_archive = True
        return world_id
    
    def loadArchives(self):
        self.archives = {}
        for name in os.listdir("archives/"):
            if os.path.isdir(os.path.join("archives", name)):
                for subfilename in os.listdir(os.path.join("archives", name)):
                    match = re.match(r'^(\d\d\d\d\-\d\d\-\d\d_\d?\d\:\d\d)$', subfilename)
                    if match:
                        when = match.groups()[0]
                        try:
                            when = datetime.datetime.strptime(when, "%Y-%m-%d_%H:%M")
                        except ValueError, e:
                            logging.log(logging.WARN, "Bad archive filename %s" % subfilename)
                            continue
                        if name not in self.archives:
                            self.archives[name] = {}
                        self.archives[name][when] = "%s/%s" % (name, subfilename)
        logging.log(logging.INFO, "Loaded %s discrete archives." % len(self.archives))
        reactor.callLater(300, self.loadArchives)
    
    def numberWithPhysics(self):
        "Returns the number of worlds with physics enabled."
        return len([world for world in self.worlds.values() if world.physics])
    
    def isAdmin(self, username):
        return username.lower() in self.admins
    
    def isBanned(self, username):
        return username.lower() in self.banned
    
    def isIpBanned(self, ip):
        return ip in self.ipbanned
    
    def addBan(self, username, reason):
        self.banned[username.lower()] = reason
    
    def removeBan(self, username):
        del self.banned[username.lower()]
    
    def banReason(self, username):
        return self.banned[username.lower()]
    
    def addIpBan(self, ip, reason):
        self.ipbanned[ip] = reason
    
    def removeIpBan(self, ip):
        del self.ipbanned[ip]
    
    def ipBanReason(self, ip):
        return self.ipbanned[ip]
    
    def world_exists(self, world_id):
        "Says if the world exists (even if unbooted)"
        return os.path.isdir("worlds/%s/" % world_id)
    
    def __del__(self):
        self.flush()



