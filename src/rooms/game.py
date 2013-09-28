
from rooms.item_registry import ItemRegistry
from rooms.area import Area


class Game(object):
    def __init__(self, owner_id, config=None):
        self._id = None
        self.owner_id = owner_id
        self.config = config or dict()
        self.running = True

        self.players = dict()
        self.area_map = dict()
        self.start_areas = []
        self.item_registry = ItemRegistry()

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
