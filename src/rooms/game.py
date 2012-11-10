
class Game(object):
    def __init__(self):
        self.area_map = dict()
        self.owner_id = None
        self.start_area_name = None
        self.open_game = True

    def start_area_id(self):
        return self.area_map[self.start_area_name]
