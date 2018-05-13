from core.aochat import server_packets
from core.decorators import instance
from tools.logger import Logger
from tools.map_object import MapObject
from __init__ import none_to_empty_string
import requests
import time


@instance()
class PorkManager:
    def __init__(self):
        self.logger = Logger("pork_manager")

    def inject(self, registry):
        self.bot = registry.get_instance("mangopie")
        self.db = registry.get_instance("db")
        self.character_manager = registry.get_instance("character_manager")

    def pre_start(self):
        self.bot.add_packet_handler(server_packets.CharacterLookup.id, self.update)
        self.bot.add_packet_handler(server_packets.CharacterName.id, self.update)

    def start(self):
        pass

    def get_character_info(self, char):
        # if we have entry in database and it is less than a day old, use that
        char_info = self.get_from_database(char)
        if char_info['source'] == "chat_server":
            char_info = None
        elif char_info and char_info['last_updated'] > (int(time.time()) - 86400):
            char_info['source'] += " (cache)"
            return char_info

        char_name = self.character_manager.resolve_char_to_name(char)
        url = "http://people.anarchy-online.com/character/bio/d/%d/name/%s/bio.xml?data_type=json" % (
            self.bot.dimension, char_name)

        r = requests.get(url)
        try:
            json = r.json()
        except ValueError as e:
            self.logger.warning("Error marshalling value as json: %s" % r.text, e)
            json = None
        if json:
            char_info_json = json[0]
            org_info_json = json[1] if json[1] else {}

            char_info = MapObject({
                "name": char_info_json["NAME"],
                "char_id": char_info_json["CHAR_INSTANCE"],
                "first_name": char_info_json["FIRSTNAME"],
                "last_name": char_info_json["LASTNAME"],
                "level": char_info_json["LEVELX"],
                "breed": char_info_json["BREED"],
                "dimension": char_info_json["CHAR_DIMENSION"],
                "gender": char_info_json["SEX"],
                "faction": char_info_json["SIDE"],
                "profession": char_info_json["PROF"],
                "profession_title": char_info_json["PROFNAME"],
                "ai_rank": char_info_json["RANK_name"],
                "ai_level": char_info_json["ALIENLEVEL"],
                "pvp_rating": char_info_json["PVPRATING"],
                "pvp_title": none_to_empty_string(char_info_json["PVPTITLE"]),
                "head_id": char_info_json["HEADID"],
                "org_id": org_info_json.get("ORG_INSTANCE", 0),
                "org_name": org_info_json.get("NAME", ""),
                "org_rank_name": org_info_json.get("RANK_TITLE", ""),
                "org_rank_id": org_info_json.get("RANK", 0),
                "source": "people.anarchy-online.com"
            })

            self.save_character_info(char_info)
            return char_info
        else:
            # return cached info from database, even tho it's old
            return char_info

    def get_character_history(self, char):
        pass

    def get_org_info(self, org_id):
        pass

    def load_character_info(self, char_id):
        char_info = self.get_character_info(char_id)
        if not char_info:
            char_info = MapObject({
                "name": "Unknown:" + str(char_id),
                "char_id": char_id,
                "first_name": "",
                "last_name": "",
                "level": 0,
                "breed": "",
                "dimension": 5,
                "gender": "",
                "faction": "",
                "profession": "",
                "profession_title": "",
                "ai_rank": "",
                "ai_level": 0,
                "pvp_rating": 0,
                "pvp_title": "",
                "head_id": 0,
                "org_id": 0,
                "org_name": "",
                "org_rank_name": "",
                "org_rank_id": 6,
                "source": "stub"
            })
            self.save_character_info(char_info)

    def save_character_info(self, char_info):
        # Remove old data
        self.db.delete('player', {'char_id': char_info.char_id})

        self.db.insert('player',
                       {
                           'char_id': char_info.char_id,
                           'name': char_info.name,
                           'first_name': char_info.first_name,
                           'last_name': char_info.last_name,
                           'level': char_info.level,
                           'breed': char_info.breed,
                           'gender': char_info.gender,
                           'faction': char_info.faction,
                           'profession': char_info.profession,
                           'profession_title ': char_info.profession_title,
                           'ai_rank': char_info.ai_rank,
                           'ai_level': char_info.ai_level,
                           'org_id': char_info.org_id,
                           'org_name': char_info.org_name,
                           'org_rank_name': char_info.org_rank_name,
                           'org_rank_id': char_info.org_rank_id,
                           'dimension': char_info.dimension,
                           'head_id': char_info.head_id,
                           'pvp_rating': char_info.pvp_rating,
                           'pvp_title': char_info.pvp_title,
                           'source': char_info.source,
                           'last_updated': int(time.time())})

    def get_from_database(self, char):
        char_id = self.character_manager.resolve_char_to_id(char)
        return self.db.find('player', {'char_id': char_id})

    def update(self, packet):
        character = self.get_from_database(packet.char_id)
        if character:
            if character['name'] != packet.name:
                self.db.update('player', {'char_id': packet.char_id}, {'name': packet.name})
        else:
            self.db.insert('player', {
                'char_id': packet.char_id,
                'name': packet.name,
                'source': 'chat_server',
                'last_updated': int(time.time())
            })
