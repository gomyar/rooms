
from rooms.timer import Timer


class Game(object):
    def __init__(self, owner_id, state):
        self.owner_id = owner_id
        self.state = state
        self.created_on = Timer.now()
        self.item_registry = None
        self._id = None

    @property
    def game_id(self):
        return self._id
