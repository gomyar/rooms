
class Game(object):
    def __init__(self):
        self.area_map = dict()
        self.owner_id = None
        self.start_areas = []
        self.open_game = True

    def start_area_map(self):
        return dict([(key, self.area_map[key]) for key in self.start_areas])

    @property
    def game_id(self):
        return str(self._id)
