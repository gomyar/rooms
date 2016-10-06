

class Game(object):
    def __init__(self, owner_id, name=None,
                 description=None):
        self.owner_id = owner_id
        self.name = name
        self.description = description
        self.item_registry = None
        self._id = None

    @property
    def game_id(self):
        return self._id
