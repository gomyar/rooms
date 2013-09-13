
from rooms.item_registry import ItemRegistry
from rooms.area import Area


class Game(object):
    def __init__(self):
        self._id = None
        self.area_map = dict()
        self.owner_id = None
        self.start_areas = []
        self.open_game = True
        self.item_registry = ItemRegistry()
        self.player_script = None
        self.players = dict()
        self.config = dict()

    @property
    def game_id(self):
        return str(self._id)

    def create_area(self, area_id, area_script=None):
        area = Area()
        area.area_id = area_id
        if area_script:
            area.load_script(area_script)
        self.area_map[area_id] = area
        area.game = self
        return area
