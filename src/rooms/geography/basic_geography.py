
from rooms.vector import time_to_position


class BasicGeography(object):
    def setup(self, room):
        pass

    def find_path(self, room, from_pos, to_pos):
        return [from_pos, to_pos]

    def get_available_position_closest_to(self, room, position):
        return position
