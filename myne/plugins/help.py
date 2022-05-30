
import random
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class HelpPlugin(ProtocolPlugin):
    
    commands = {
        "help": "commandHelp",
        "cmdlist": "commandCmdlist",
    }
    
    def commandHelp(self, parts):
        "/help - This."
        if len(parts) > 1:
            try:
                func = self.client.commands[parts[1].lower()]
            except KeyError:
                if parts[1].lower() == "basics":
                    self.client.sendServerMessage("/worlds - Lists all worlds you can enter")
                    self.client.sendServerMessage("/load worldname - Takes you to another world.")
                    self.client.sendServerMessage("Step through portals to teleport around.")
                    self.client.sendServerMessage("/tp username - This works for EVERYONE")
                    self.client.sendNormalMessage(COLOUR_RED+"global admin "+COLOUR_GREEN+"world op "+COLOUR_CYAN+"writer "+COLOUR_GREY+"normal "+COLOUR_PURPLE+"from irc")
                else:
                    self.client.sendServerMessage("Unknown command '%s'" % parts[1])
            else:
                if func.__doc__:
                    self.client.sendServerMessage(func.__doc__)
                else:
                    self.client.sendServerMessage("There's no help for that command.")
        else:
            self.client.sendNormalMessage("Server info: "+COLOUR_PURPLE+self.client.factory.info_url)
            self.client.sendServerMessage("For specific help, type /help command")
            self.client.sendServerMessage("For basic help, type /help basics")
            self.client.sendServerMessage("Use @username message for private messaging.")    
            self.client.sendServerMessage("To see a list of commands, type /cmdlist")
    
    def commandCmdlist(self, parts):
        "/cmdlist - Shows a list of all commands."
        commands = []
        for name, command in self.client.commands.items():
            if getattr(command, "admin_only", False) and not self.client.isAdmin():
                continue
            if getattr(command, "op_only", False) and not self.client.isOp():
                continue
            if getattr(command, "writer_only", False) and not self.client.isWriter():
                continue
            commands.append(name)
        self.client.sendServerList(sorted(commands))
    