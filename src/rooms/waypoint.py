
import time
import math

import logging
log = logging.getLogger("rooms.path")


def get_now():
    return time.time()


def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)


def path_from_waypoints(point_list, speed):
    path = []
    last_x, last_y = point_list[0]
    current_time = get_now()
    path.append( (last_x, last_y, current_time ) )
    for point in point_list[1:]:
        x, y = point
        current_time += distance(last_x, last_y, x, y) / speed
        path.append( (x, y, current_time ) )
        last_x, last_y = x, y
    return Path(path)


class Path(object):
    def __init__(self, waypoints=None):
        self.path = waypoints or []

    def __repr__(self):
        return "Path(%s)" % (self.path,)

    def set_position(self, position):
        x, y = position
        self.path = [ (x, y, get_now() ), (x, y, get_now() ) ]

    def path_end_time(self):
        return self.path[-1][2]

    def path_end_position(self):
        return self.path[-1][:2]

    def basic_path_list(self):
        return [(p[0], p[1]) for p in self.path]

    def position(self):
        return (self.x(), self.y())

    def speed(self):
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
        diff_t = end_time - start_time
        if diff_t <= 0:
            return end_x
        return diff_t / distance(start_x, start_y, end_x, end_y)

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
