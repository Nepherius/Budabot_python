from core.decorators import instance
from core.logger import Logger
from .setting_types import SettingType
from core.registry import Registry
from __init__ import get_attrs
import os


@instance()
class SettingManager:
    def __init__(self):
        self.logger = Logger("setting_manager")
        self.settings = {}

    def inject(self, registry):
        self.db = registry.get_instance("db")
        self.util = registry.get_instance("util")

    def start(self):
        self.db.load_sql_file("setting.sql", os.path.dirname(__file__))
        self.db.exec("UPDATE setting SET verified = 0")

    def post_start(self):
        # process decorators
        for _, inst in Registry.get_all_instances().items():
            for name, method in get_attrs(inst).items():
                if hasattr(method, "setting"):
                    setting_name, value, description, obj = getattr(method, "setting")
                    handler = getattr(inst, name)
                    module = self.util.get_module_name(handler)
                    self.register(setting_name, value, description, obj, module)

        self.db.exec("DELETE FROM event_config WHERE verified = 0")

    def register(self, name, value, description, setting, module):
        name = name.lower()
        module = module.lower()
        setting.set_name(name)

        if not description:
            self.logger.warning("No description specified for setting '%s'" % name)

        row = self.db.query_single("SELECT name, value, description FROM setting WHERE name = ?",
                                   [name])

        if row is None:
            # add new event commands
            self.db.exec(
                "INSERT INTO setting (name, value, description, module, verified) VALUES (?, ?, ?, ?, ?)",
                [name, value, description, module, 1])
        else:
            # mark command as verified
            self.db.exec(
                "UPDATE setting SET description = ?, verified = ?, module = ? WHERE name = ?",
                [description, 1, module, name])

        self.settings[name] = setting

    def get_value(self, name):
        row = self.db.query_single("SELECT value FROM setting WHERE name = ?", [name])
        return row.value if row else None

    def set_value(self, name, value):
        self.db.exec("UPDATE setting SET value = ? WHERE name = ?", [value, name])

    def get(self, name):
        name = name.lower()
        setting = self.settings.get(name, None)
        if setting:
            return setting
        else:
            return None
