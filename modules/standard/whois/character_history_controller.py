from core.decorators import instance, command
from core.db import DB
from core.text import Text
from core.commands.param_types import Any, Int


@instance()
class CharacterHistoryController:
    def __init__(self):
        pass

    def inject(self, registry):
        self.db = registry.get_instance("db")
        self.text = registry.get_instance("text")
        self.pork_manager = registry.get_instance("pork_manager")

    @command(command="history", params=[Any("character"), Int("server_num")], access_level="all",
             description="Get history of character for a specific server num")
    def handle_history_cmd1(self, channel, sender, reply, args):
        name = args[1].capitalize()
        server_num = args[2]
        reply(self.get_character_history(name, server_num))

    @command(command="history", params=[Any("character")], access_level="all",
             description="Get history of character for the current server num", sub_command="list")
    def handle_history_cmd2(self, channel, sender, reply, args):
        name = args[1].capitalize()
        reply(self.get_character_history(name, 5))

    def get_character_history(self, name, server_num):
        return "<header>" + name + " (" + str(server_num) + ")<end>"

