"""
Decorators for protocol (command) methods.
"""

def admin_only(func):
    "Decorator for admin-only command methods."
    func.admin_only = True
    return func

def op_only(func):
    "Decorator for op-only command methods."
    func.op_only = True
    return func

def writer_only(func):
    "Decorator for writer-only command methods."
    func.writer_only = True
    return func

def username_command(func):
    "Decorator for commands that accept a single username parameter, and need a Client"
    def inner(self, parts):
        if len(parts) == 1:
            self.client.sendServerMessage("Please specify a username.")
        else:
            username = parts[1].lower()
            if username not in self.client.factory.usernames:
                self.client.sendServerMessage("No such user '%s'" % username)
            else:
                if len(parts) > 2:
                    func(self, self.client.factory.usernames[username], parts[2:])
                else:
                    func(self, self.client.factory.usernames[username])
    inner.__doc__ = func.__doc__
    return inner

def only_string_command(string_name):
    def only_inner(func):
        "Decorator for commands that accept a single username/plugin/etc parameter, and don't need it checked"
        def inner(self, parts):
            if len(parts) == 1:
                self.client.sendServerMessage("Please specify a %s." % string_name)
            else:
                username = parts[1].lower()
                if len(parts) > 2:
                    func(self, username, parts[2:])
                else:
                    func(self, username)
        inner.__doc__ = func.__doc__
        return inner
    return only_inner

only_username_command = only_string_command("username")

def username_world_command(func):
    "Decorator for commands that accept a single username parameter and possibly a world name."
    def inner(self, parts):
        if len(parts) == 1:
            self.client.sendServerMessage("Please specify a username.")
        else:
            username = parts[1].lower()
            if len(parts) == 3:
                try:
                    world = self.client.factory.worlds[parts[2].lower()]
                except KeyError:
                    self.client.sendServerMessage("Unknown world '%s'." % parts[2].lower())
                    return
            else:
                world = self.client.world
            func(self, username, world)
    inner.__doc__ = func.__doc__
    return inner

def on_off_command(func):
    "Decorator for commands that accept a single on/off parameter"
    def inner(self, parts):
        if len(parts) == 1:
            self.client.sendServerMessage("Please specify 'on' or 'off'.")
        else:
            if parts[1].lower() not in ["on", "off"]:
                self.client.sendServerMessage("Use 'on' or 'off', not '%s'" % parts[1])
            else:
                func(self, parts[1].lower())
    inner.__doc__ = func.__doc__
    return inner