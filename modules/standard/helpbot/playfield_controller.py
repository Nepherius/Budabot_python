from core.decorators import instance, command, event
from core.db import DB
from core.text import Text
import os


@instance()
class PlayfieldController:
    def __init__(self):
        pass

    def inject(self, registry):
        self.db = registry.get_instance("db")
        self.text = registry.get_instance("text")

    def start(self):
        self.db.load_sql_file("playfields.sql", os.path.dirname(__file__))
