
class Game(object):
    def __init__(self, owner_id):
        self.owner_id = owner_id
        self._id = None

    @property
    def game_id(self):
        return self._id
