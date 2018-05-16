from core.decorators import instance, command
from core.db import DB
from tools.text import Text
from tools.chat_blob import ChatBlob
from tools.command_param_types import Const, Any, Options
from operator import itemgetter


@instance()
class ConfigController:
    def __init__(self):
        pass

    def inject(self, registry):
        self.db: DB = registry.get_instance("db")
        self.text: Text = registry.get_instance("text")
        self.access_manager = registry.get_instance("access_manager")
        self.command_manager = registry.get_instance("command_manager")
        self.event_manager = registry.get_instance("event_manager")
        self.setting_manager = registry.get_instance("setting_manager")

    def start(self):
        pass

    @command(command="config", params=[], access_level="superadmin",
             description="Shows configuration options for the bot")
    def config_list_cmd(self, channel, sender, reply, args):
        pipeline = [
            {
                '$project': {
                    'module': 1,
                    'count_enabled': {
                        '$cond': {'if': {'$eq': ['$enabled', 1]}, 'then': 1, 'else': 0}
                    },
                    'count_disabled': {
                        '$cond': {'if': {'$eq': ['$enabled', 0]}, 'then': 1, 'else': 0}
                    }
                }
            }, {
                '$group': {
                    '_id': '$module', 'count_enabled': {'$sum': '$count_enabled'},
                    'count_disabled': {'$sum': '$count_disabled'}
                }
            }, {
                '$sort': {'_id': 1}
            }
        ]
        cmd_config = self.db.client['command_config'].aggregate(pipeline)
        event_config = self.db.client['event_config'].aggregate(pipeline)
        settings = self.db.client['settings'].aggregate(pipeline)

        final_list = []
        lists = [cmd_config, event_config, settings]
        for lst in lists:
            for dct in lst:
                id_to_lookup = dct['_id']
                found_duplicate_flag = 0
                for final_dict in final_list:
                    if final_dict['_id'] == id_to_lookup:
                        found_duplicate_flag = 1
                        final_dict['count_enabled'] += dct['count_enabled']
                        final_dict['count_disabled'] += dct['count_disabled']
                        break
                if found_duplicate_flag == 0:
                    final_list.append(dct)
        count = 0
        blob = ""
        current_group = ""
        for row in sorted(final_list, key=itemgetter('_id')):
            count += 1
            parts = row['_id'].split(".")
            group = parts[0]
            module = parts[1]
            if group != current_group:
                current_group = group
                blob += "\n<header2>" + current_group + "<end>\n"

            blob += self.text.make_chatcmd(module, "/tell <myname> config mod " + row['_id']) + " "
            if row['count_enabled'] > 0 and row['count_disabled'] > 0:
                blob += "<yellow>Partial<end>"
            elif row['count_disabled'] == 0:
                blob += "<green>Enabled<end>"
            else:
                blob += "<red>Disabled<end>"
            blob += "\n"

        reply(ChatBlob("Config (%d)" % count, blob))

    @command(command="config", params=[Const("mod"), Any("module_name")], access_level="superadmin",
             description="Shows configuration options for a specific module")
    def config_module_list_cmd(self, channel, sender, reply, args):
        module = args[1].lower()

        blob = ""

        data = self.db.client['settings'].find({'module': module}).sort('name', 1)
        data = list(data)
        if data:
            blob += "<header2>Settings<end>\n"
            for row in data:
                setting = self.setting_manager.get(row['name'])
                blob += setting.get_description() + ": " + self.text.make_chatcmd(setting.get_display_value(),
                                                                                  "/tell <myname> config setting " +
                                                                                  row['name']) + "\n"

        data = self.db.client['command_config'].find({'module': module}, {'_id': 0, 'channel': 0}).sort('command', 1)
        d = list(data)
        data = [i for n, i in enumerate(d) if i not in d[n + 1:]]
        if data:
            blob += "\n<header2>Commands<end>\n"
            for row in data:
                command_key = self.command_manager.get_command_key(row['command'], row['sub_command'])
                blob += self.text.make_chatcmd(command_key, "/tell <myname> config cmd " + command_key) + "\n"

        data = self.db.client['event_config'].find({'module': module}).sort([('event_type', 1), ('handler', 1)])
        data = list(data)
        if data:
            blob += "\n<header2>Events<end>\n"
            for row in data:
                event_type_key = self.event_manager.get_event_type_key(row['event_type'], row['event_sub_type'])
                blob += row['event_type'] + " - " + row['description']
                blob += " " + self.text.make_chatcmd("On",
                                                     "/tell <myname> config event " + event_type_key + " " + row[
                                                         'handler'] + " enable")
                blob += " " + self.text.make_chatcmd("Off",
                                                     "/tell <myname> config event " + event_type_key + " " + row[
                                                         'handler'] + " disable")
                blob += "\n"

        if blob:
            reply(ChatBlob("Module (" + module + ")", blob))
        else:
            reply("Could not find module <highlight>%s<end>" % module)

    @command(command="config",
             params=[Const("event"), Any("event_type"), Any("event_handler"), Options(["enable", "disable"])],
             access_level="superadmin",
             description="Enable or disable an event")
    def config_event_status_cmd(self, channel, sender, reply, args):
        event_type = args[1].lower()
        event_handler = args[2].lower()
        action = args[3].lower()
        event_base_type, event_sub_type = self.event_manager.get_event_type_parts(event_type)
        enabled = 1 if action == "enable" else 0

        if not self.event_manager.is_event_type(event_base_type):
            reply("Unknown event type <highlight>%s<end>." % event_type)
            return

        count = self.db.update('event_config', {'event_type': event_base_type, 'event_sub_type': event_sub_type,
                                                'handler': event_handler}, {
                                   'enabled': enabled
                               })
        if count.matched_count == 0:
            reply("Could not find event for type <highlight>%s<end> and handler <highlight>%s<end>." % (
                event_type, event_handler))
        else:
            reply(
                "Event type <highlight>%s<end> for handler <highlight>%s<end> has been <highlight>%sd<end> successfully." % (
                    event_type, event_handler, action))

    @command(command="config", params=[Const("setting"), Any("setting_name"), Any("new_value")],
             access_level="superadmin",
             description="Sets new value for a setting")
    def config_setting_update_cmd(self, channel, sender, reply, args):
        setting_name = args[1].lower()
        new_value = args[2]
        setting = self.setting_manager.get(setting_name)
        if setting:
            try:
                setting.set_value(new_value)
                reply("Setting <highlight>%s<end> has been set to <highlight>%s<end>." % (setting_name, new_value))
            except Exception as e:
                reply("Error! %s" % str(e))
        else:
            reply("Could not find setting <highlight>%s<end>." % setting_name)

    @command(command="config", params=[Const("setting"), Any("setting_name")], access_level="superadmin",
             description="Shows configuration options for a setting")
    def config_setting_show_cmd(self, channel, sender, reply, args):
        setting_name = args[1].lower()

        blob = ""

        setting = self.setting_manager.get(setting_name)

        if setting:
            blob += "Current Value: <highlight>%s<end>\n" % str(setting.get_display_value())
            blob += "Description: <highlight>%s<end>\n\n" % setting.get_description()
            blob += setting.get_display()
            reply(ChatBlob("Setting (%s)" % setting_name, blob))
        else:
            reply("Could not find setting <highlight>%s<end>." % setting_name)
