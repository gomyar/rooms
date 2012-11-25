
import time
import math

import logging
log = logging.getLogger("rooms.path")


def get_now():
    return time.time()


def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)


class Path(object):
    def __init__(self, position=(0, 0)):
        self.speed = 150.0
        self.set_position(position)

    def set_position(self, position):
        x, y = position
        self.path = [ (x, y, get_now() ), (x, y, get_now() ) ]

    def path_array(self):
        return self.path

    def time_to_move(self, x1, y1, x2, y2):
        return distance(x1, y1, x2, y2) / self.speed

    def path_end_time(self):
        return self.path[-1][2]

    def path_end_position(self):
        return self.path[-1][:2]

    def set_path(self, path):
        self.path = []
        last_x, last_y = path[0]
        current_time = get_now()
        self.path.append( (last_x, last_y, current_time ) )
        for point in path[1:]:
            x, y = point
            current_time += self.time_to_move(last_x, last_y, x, y)
            self.path.append( (x, y, current_time ) )
            last_x, last_y = x, y

    def basic_path_list(self):
        return [(p[0], p[1]) for p in self.path]

    def position(self):
        return (self.x(), self.y())

    def x(self):
        now = get_now()
        path = list(self.path)
        start = path[0]
        while path and now > path[0][2]:
            start = path.pop(0)
        if not path:
            return self.path[-1][0]
        start_x, start_y, start_time = start
        end_x, end_y, end_time = path[0]

        if now > end_time:
            return end_x
        diff_x = end_x - start_x
        diff_t = end_time - start_time
        if diff_t <= 0:
            return end_x
        inc = (now - start_time) / diff_t
        return start_x + diff_x * inc

    def y(self):
        now = get_now()
        path = list(self.path)
        start = path[0]
        while path and now > path[0][2]:
            start = path.pop(0)
        if not path:
            return self.path[-1][1]
        start_x, start_y, start_time = start
        end_x, end_y, end_time = path[0]

        if now > end_time:
            return end_y
        diff_y = end_y - start_y
        diff_t = end_time - start_time
        if diff_t <= 0:
            return end_y
        inc = (now - start_time) / diff_t
        return start_y + diff_y * inc
