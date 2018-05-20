from core.decorators import instance
from core.command_manager import CommandManager
from tools.logger import Logger


@instance()
class CommandAliasManager:
    def __init__(self):
        self.logger = Logger("command_alias_manager")

    def inject(self, registry):
        self.db = registry.get_instance("db")
        self.command_manager: CommandManager = registry.get_instance("command_manager")

    def check_for_alias(self, command_str):
        row = self.get_alias(command_str)
        if row and row['enabled']:
            return row['command']
        else:
            return None

    def get_alias(self, alias):
        return self.db.find('command_alias', {'alias': alias})

    def add_alias(self, alias, command):
        row = self.get_alias(alias)
        if row:
            if row['enabled']:
                return False
            else:
                self.db.update('command_alias', {'alias': alias}, {'command': command, 'enabled': 1})
                return True
        else:
            self.db.insert('command_alias', {'alias': alias, 'command': command, 'enabled': 1})
            return True

    def remove_alias(self, alias):
        row = self.get_alias(alias)
        if row:
            if row['enabled']:
                self.db.update('command_alias', {'alias': alias}, {'enabled': 0})
                return True
            else:
                return False
        else:
            return False

    def get_enabled_aliases(self):
        return self.db.find_all('command_alias', {'enabled': 1})
