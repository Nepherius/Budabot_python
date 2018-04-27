from core.decorators import instance
from core.registry import Registry
from tools.logger import Logger
from __init__ import get_attrs
import time
import os


@instance()
class EventManager:
    def __init__(self):
        self.handlers = {}
        self.logger = Logger("event_manager")
        self.event_types = []
        self.last_timer_event = 0

    def inject(self, registry):
        self.db = registry.get_instance("db")
        self.util = registry.get_instance("util")

    def pre_start(self):
        self.register_event_type("timer")

    def start(self):
        # process decorators
        for _, inst in Registry.get_all_instances().items():
            for name, method in get_attrs(inst).items():
                if hasattr(method, "event"):
                    event_type, description = getattr(method, "event")
                    handler = getattr(inst, name)
                    module = self.util.get_module_name(handler)
                    self.register(handler, event_type, description, module)

    def register_event_type(self, event_type):
        event_type = event_type.lower()

        if event_type in self.event_types:
            self.logger.error("Could not register event type '%s': event type already registered" % event_type)
            return

        self.logger.debug("Registering event type '%s'" % event_type)
        self.event_types.append(event_type)

    def is_event_type(self, event_base_type):
        return event_base_type in self.event_types

    def register(self, handler, event_type, description, module):
        event_base_type, event_sub_type = self.get_event_type_parts(event_type)
        module = module.lower()
        handler_name = self.util.get_handler_name(handler).lower()

        if event_base_type not in self.event_types:
            self.logger.error("Could not register handler '%s' for event type '%s': event type does not exist" % (
                handler_name, event_type))
            return

        if not description:
            self.logger.warning("No description for event_type '%s' and handler '%s'" % (event_type, handler_name))

        row = self.db.find('event_config', {'event_type': event_base_type, 'handler': handler_name})

        if row is None:
            # add new event commands
            self.db.insert('event_config', {
                'event_type': event_base_type,
                'event_sub_type': event_sub_type,
                'handler': handler_name,
                'description': description,
                'module': module,
                'verified': 1,
                'enabled': 1
            })

            if event_base_type == "timer":
                self.db.insert('timer_event', {
                    'event_type': event_base_type,
                    'event_sub_type': event_sub_type,
                    'handler': handler_name,
                    'next_run': int(time.time())
                })
        else:
            # mark command as verified
            self.db.update('event_config', {
                'event_type': event_base_type,
                'handler': handler_name
            },{
                'verified': 1,
                'module': module,
                'description': description,
                'event_sub_type': event_sub_type,
            })

            if event_base_type == "timer":
                self.db.update('timer_event', {
                    'event_type': event_base_type,
                    'handler': handler_name
                }, {
                    'event_sub_type': event_sub_type
                })

        # load command handler
        self.handlers[handler_name] = handler

    def fire_event(self, event_type, event_data=None):
        event_base_type, event_sub_type = self.get_event_type_parts(event_type)

        if event_base_type not in self.event_types:
            self.logger.error("Could not fire event type '%s': event type does not exist" % event_type)
            return

        data = self.db.find_all('event_config', {
            'event_type': event_base_type,
            'event_sub_type': event_sub_type,
            'enabled': 1
        })
        for row in data:
            handler = self.handlers.get(row['handler'], None)
            if not handler:
                self.logger.error(
                    "Could not find handler callback for event type '%s' and handler '%s'" % (event_type, row.handler))
                return

            handler(event_type, event_data)

    def get_event_type_parts(self, event_type):
        parts = event_type.lower().split(":", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            return parts[0], ""

    def get_event_type_key(self, event_base_type, event_sub_type):
        return event_base_type + ":" + event_sub_type

    def check_for_timer_events(self):
        pass
        # timestamp = int(time.time())

        # # timer events will execute not more often than once per second
        # if self.last_timer_event == timestamp:
        #     return
        #
        # self.last_timer_event = timestamp
        #
        # data = self.db.query("SELECT e.event_type, e.event_sub_type, e.handler, t.next_run FROM timer_event t "
        #                      "JOIN event_config e ON t.event_type = e.event_type AND t.handler = e.handler "
        #                      "WHERE t.next_run <= ? AND e.enabled = 1", [timestamp])
        # for row in data:
        #     event_type_key = self.get_event_type_key(row.event_type, row.event_sub_type)
        #
        #     # timer event run times should be consistent, so we base the next run time off the last run time,
        #     # instead of the current timestamp
        #     next_run = row.next_run + int(row.event_sub_type)
        #
        #     # prevents timer events from getting too far behind, or having a large "catch-up" after
        #     # the bot has been offline for a time
        #     if next_run < timestamp:
        #         next_run = timestamp + int(row.event_sub_type)
        #
        #     self.db.exec("UPDATE timer_event SET next_run = ? WHERE event_type = ? AND handler = ?",
        #                  [next_run, row.event_type, row.handler])
        #
        #     self.fire_event(event_type_key)
