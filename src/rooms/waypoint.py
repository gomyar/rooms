
import time
import math

from rooms.timing import get_now

import logging
log = logging.getLogger("rooms.path")


def distance(from_pos, to_pos):
    return math.hypot(to_pos.x - from_pos.x, to_pos.y - from_pos.y)


def path_from_waypoints(point_list, speed):
    path = []
    last_point = point_list[0]
    current_time = get_now()
    path.append( (last_point, current_time ) )
    for point in point_list[1:]:
        current_time += distance(last_point, point) / speed
        path.append( (P(point.x, point.y), current_time ) )
        last_point = point
    return Path(path)


class Path(object):
    def __init__(self, waypoints=None):
        self.path = waypoints or []

    def __repr__(self):
        return "Path(%s)" % (self.path,)

    def __eq__(self, rhs):
        return rhs and type(rhs) is Path and self.path == rhs.path

    def set_position(self, position):
        self.path = [ (position, get_now() ), (position, get_now() ) ]

    def path_end_time(self):
        return self.path[-1][1]

    def basic_path_list(self):
        return [p for (p, t) in self.path]

    def position(self):
        return P(self.x(), self.y())

    def speed(self):
        now = get_now()
        path = list(self.path)
        start = path.pop(0)
        while path and now > path[0][1]:
            start = path.pop(0)
        if len(path) > 0:
            end = path[0]
            start_point, start_time = start
            end_point, end_time = end
            if now > end_time:
                return 0
            else:
                dist = distance(start_point, end_point)
                taken = end_time - start_time
                return dist / taken if taken else 0
        else:
            return 0

    def x(self):
        now = get_now()
        path = list(self.path)
        start = path[0]
        while path and now > path[0][1]:
            start = path.pop(0)
        if not path:
            return self.path[-1][0].x
        start_point, start_time = start
        end_point, end_time = path[0]

        if now > end_time:
            return end_point.x
        diff_x = end_point.x - start_point.x
        diff_t = end_time - start_time
        if diff_t <= 0:
            return end_point.x
        inc = (now - start_time) / diff_t
        return start_point.x + diff_x * inc

    def y(self):
        now = get_now()
        path = list(self.path)
        start = path[0]
        while path and now > path[0][1]:
            start = path.pop(0)
        if not path:
            return self.path[-1][0].y
        start_point, start_time = start
        end_point, end_time = path[0]

        if now > end_time:
            return end_point.y
        diff_y = end_point.y - start_point.y
        diff_t = end_time - start_time
        if diff_t <= 0:
            return end_point.y
        inc = (now - start_time) / diff_t
        return start_point.y + diff_y * inc
