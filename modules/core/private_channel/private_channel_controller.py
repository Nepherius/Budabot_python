from core.decorators import instance, command, event
from tools.command_param_types import Any
from core.private_channel_manager import PrivateChannelManager


@instance()
class PrivateChannelController:
    def __init__(self):
        pass

    def inject(self, registry):
        self.bot = registry.get_instance("mangopie")
        self.private_channel_manager = registry.get_instance("private_channel_manager")
        self.character_manager = registry.get_instance("character_manager")

    @command(command="join", params=[], access_level="all",
             description="Join the private channel")
    def join_cmd(self, channel, sender, reply, args):
        self.private_channel_manager.invite(sender.char_id)

    @command(command="leave", params=[], access_level="all",
             description="Leave the private channel")
    def leave_cmd(self, channel, sender, reply, args):
        self.private_channel_manager.kick(sender.char_id)

    @command(command="invite", params=[Any("character")], access_level="all",
             description="Invite a character to the private channel")
    def invite_cmd(self, channel, sender, reply, args):
        char = args[1].capitalize()
        char_id = self.character_manager.resolve_char_to_id(char)
        if sender.char_id == char_id:
            self.private_channel_manager.invite(sender.char_id)
        elif char_id:
            self.bot.send_private_message(char_id, "You have been invited to the private channel by <highlight>%s<end>." % sender.name)
            self.private_channel_manager.invite(char_id)
            reply("You have invited <highlight>%s<end> to the private channel." % char)
        else:
            reply("Could not find character <highlight>%s<end>." % char)

    @event(PrivateChannelManager.JOINED_PRIVATE_CHANNEL_EVENT, "Notify private channel when someone joins")
    def private_channel_joined_event(self, event_type, event_data):
        char_name = self.character_manager.get_char_name(event_data.char_id)
        self.bot.send_private_channel_message("<highlight>%s<end> has joined the private channel." % char_name)

    @event(PrivateChannelManager.LEFT_PRIVATE_CHANNEL_EVENT, "Notify private channel when someone leaves")
    def private_channel_left_event(self, event_type, event_data):
        char_name = self.character_manager.get_char_name(event_data.char_id)
        self.bot.send_private_channel_message("<highlight>%s<end> has left the private channel." % char_name)
