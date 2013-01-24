
from rooms.item_registry import ItemRegistry


class Game(object):
    def __init__(self):
        self.area_map = dict()
        self.owner_id = None
        self.start_areas = []
        self.open_game = True
        self.item_registry = ItemRegistry()
        self.player_script = None

    @property
    def game_id(self):
        return str(self._id)
