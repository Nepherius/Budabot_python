from core.decorators import instance
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from pymongo import monitoring
from tools.logger import Logger
import json

@instance()
class DB:
    def __init__(self):
        self.connection = None
        self.client = None
        self.logger = Logger("MongoDB")

    def connect(self, host, name):
        self.connection = MongoClient('mongodb://%s' % host)  # event_listeners=[CommandLogger()]
        self.client = self.connection[name]
        # Test db connection on start up, do not remove
        self.connection.admin.command('ismaster')

    def insert(self, table, query):
        try:
            return self.client[table].insert_one(query)
        except DuplicateKeyError:
            self.logger.warning('Duplicate error')
            return False

    def update(self, table, target, newVal):
        return self.client[table].update_one(target, {"$set": newVal})

    def update_all(self, table, target, newVal):
        return self.client[table].update_many(target, {"$set": newVal})

    def find(self, table, query, params=None):
        return self.client[table].find_one(query)

    def find_all(self, table, query):
        return self.client[table].find(query).sort("module")

    def delete(self, table, query):
        return self.client[table].delete_one(query)

    def delete_all(self, table, query):
        return self.client[table].delete_many(query)


class CommandLogger(monitoring.CommandListener):
    def __init__(self):
        self.logger = Logger("MongoDb")

    def started(self, event):
        self.logger.debug("Command {0.command_name} with request id "
                          "{0.request_id} started on server "
                          "{0.connection_id}".format(event))

    def succeeded(self, event):
        self.logger.debug("Command {0.command_name} with request id "
                          "{0.request_id} on server {0.connection_id} "
                          "succeeded in {0.duration_micros} "
                          "microseconds".format(event))

    def failed(self, event):
        self.logger.debug("Command {0.command_name} with request id "
                          "{0.request_id} on server {0.connection_id} "
                          "failed in {0.duration_micros} "
                          "microseconds".format(event))
