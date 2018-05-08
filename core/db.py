from core.decorators import instance
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from tools.logger import Logger


@instance()
class DB:
    def __init__(self):
        self.connection = None
        self.client = None
        self.logger = Logger("MongoDB")

    def connect(self, host, name):
        self.connection = MongoClient('mongodb://%s' % host)
        self.client = self.connection[name]
        # Test db connection on start up, do not remove
        self.connection.admin.command('ismaster')

    def insert(self, table, query):
        try:
            return self.client[table].insert_one(query)
        except DuplicateKeyError:
            self.logger.warning('Duplicate error')
            return False

    def update(self, table, target, update):
        return self.client[table].update_one(target, {"$set": update})

    def update_all(self, table, target, update):
        return self.client[table].update_many(target, {"$set": update})

    def find(self, table, query):
        return self.client[table].find_one(query)

    def find_all(self, table, query):
        return self.client[table].find(query)

    def delete(self, table, query):
        return self.client[table].delete_one(query)

    def delete_all(self, table, query):
        return self.client[table].delete_many(query)
