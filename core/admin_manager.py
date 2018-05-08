from core.decorators import instance


@instance()
class AdminManager:
    ADMIN = "admin"
    MODERATOR = "moderator"

    def __init__(self):
        pass

    def inject(self, registry):
        self.db = registry.get_instance("db")
        self.access_manager = registry.get_instance("access_manager")

    def pre_start(self):
        self.access_manager.register_access_level(self.ADMIN, 20, self.check_admin)
        self.access_manager.register_access_level(self.MODERATOR, 30, self.check_mod)

    def start(self):
        pass

    def check_admin(self, char_id):
        access_level = self.get_access_level(char_id)
        return access_level == self.ADMIN

    def check_mod(self, char_id):
        access_level = self.get_access_level(char_id)
        return access_level == self.MODERATOR

    def get_access_level(self, char_id):
        row = self.db.find('admin', {'char_id': char_id})
        if row:
            return row['access_level']
        else:
            return None

    def add(self, char_id, access_level):
        if access_level in [self.MODERATOR, self.ADMIN]:
            # remove any existing admin access level first
            self.remove(char_id)
            self.db.insert('admin', {'char_id': char_id, 'access_level': access_level})
            return True
        else:
            return False

    def remove(self, char_id):
        return self.db.delete_all('admin', {'char_id': char_id})

    def get_all(self):
        return self.db.client['admin'].aggregate([
            {'$lookup':
                 {'from': 'player',
                  'localField': 'char_id',
                  'foreignField': 'char_id',
                  'as': 'char'
                  }
             }
        ])
