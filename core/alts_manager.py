from core.decorators import instance
import os


@instance()
class AltsManager:
    UNVALIDATED = 0
    VALIDATED = 1
    MAIN = 2

    def __init__(self):
        pass

    def inject(self, registry):
        self.db = registry.get_instance("db")
        self.character_manager = registry.get_instance("character_manager")
        self.pork_manager = registry.get_instance("pork_manager")

    def start(self):
        pass

    def get_alts(self, char_id):
        return self.db.client['alts'].aggregate([
            {
                '$match': {
                    'group_id': self.get_group_id(char_id)
                }
            },
            {'$lookup':
                 {'from': 'player',
                  'localField': 'char_id',
                  'foreignField': 'char_id',
                  'as': 'char'
                  }
             }
        ])

    def add_alt(self, sender_char_id, alt_char_id):
        alt_row = self.get_alt_status(alt_char_id)
        if alt_row:
            return False

        sender_row = self.get_alt_status(sender_char_id)
        if sender_row:
            if sender_row['status'] == self.MAIN or sender_row['status'] == self.VALIDATED:
                params = [alt_char_id, sender_row['group_id'], self.VALIDATED]
            else:
                params = [alt_char_id, sender_row['group_id'], self.UNVALIDATED]
        else:
            # main does not exist, create entry for it
            group_id = self.get_next_group_id()
            self.db.insert('alts', {'char_id': sender_char_id, 'group_id': group_id, 'status': self.MAIN})

            # make sure char info exists in character table
            self.pork_manager.load_character_info(sender_char_id)

            params = [alt_char_id, group_id, self.VALIDATED]

        # make sure char info exists in character table
        self.pork_manager.load_character_info(alt_char_id)
        self.db.insert('alts', {'char_id': params[0], 'group_id': params[1], 'status': params[2]})
        return True

    def remove_alt(self, sender_char_id, alt_char_id):
        alt_row = self.get_alt_status(alt_char_id)
        sender_row = self.get_alt_status(sender_char_id)

        # sender and alt do not belong to the same group id
        if not alt_row or not sender_row or alt_row['group_id'] != sender_row['group_id']:
            return False

        # cannot remove alt from an unvalidated sender
        if sender_row['status'] == self.UNVALIDATED:
            return False

        self.db.delete('alts', {'char_id': alt_char_id})
        return True

    def get_alt_status(self, char_id):
        return self.db.find('alts', {'char_id': char_id})

    def get_group_id(self, char_id):
        row = self.db.find('alts', {'char_id': char_id})
        return row['group_id']

    def get_next_group_id(self):
        row = list(self.db.client['alts'].find().sort('group_id', -1).limit(1))
        return int(row[0]['group_id']) + 1 if row else 1
