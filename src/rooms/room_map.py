

class MapRoom(object):
    def __init__(self):
        self.topleft = Position()
        self.bottomright = Position()
        self.doors = dict()
        self.room_objects = dict()
        self.tags = dict()


class Map(object):
    def __init__(self, map_id, rooms=None):
        self.map_id
        self.rooms = rooms or []
