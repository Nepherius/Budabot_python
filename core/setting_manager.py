from core.decorators import instance
from tools.logger import Logger
from tools.setting_types import SettingType
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
        # process decorators
        for _, inst in Registry.get_all_instances().items():
            for name, method in get_attrs(inst).items():
                if hasattr(method, "setting"):
                    setting_name, value, description, obj = getattr(method, "setting")
                    handler = getattr(inst, name)
                    module = self.util.get_module_name(handler)
                    self.register(setting_name, value, description, obj, module)

    def register(self, name, value, description, setting: SettingType, module):
        name = name.lower()
        module = module.lower()
        setting.set_name(name)

        if not description:
            self.logger.warning("No description specified for setting '%s'" % name)

        result = self.db.find('settings', {"name": name})

        if result is None:
            # add new event commands
            self.db.insert("settings",
                           {"name": name, "value": value, "description": description, "module": module, "verified": 1})
        else:
            # mark command as verified
            self.db.update('settings', {"name": name}, {"description": description, "verified": 1, "module": module})

        self.settings[name] = setting

    def get_value(self, name):
        result = self.db.find('settings', {"name": name})

        return result['value'] if result else None

    def set_value(self, name, value):
        self.db.update('settings', {"name": name}, {"value": value})

    def get(self, name):
        name = name.lower()
        setting = self.settings.get(name, None)
        if setting:
            return setting
        else:
            return None
