
import time
import math


def _get_now():
    return time.time()


def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def calculate_time_to_dest(startposition, destination, speed):
    if speed == 0.0:
        return 0.0
    distance = math.hypot(destination[0] - startposition[0],
        destination[1] - startposition[1])
    return distance / speed


def plot_intercept_point(position, speed, targetPos, targetDest,
        targetSpeed):
    target_start_point = targetPos
    halfway_point = targetDest
    for i in range(20):
        halfway_point = (targetPos[0] + (targetDest[0] - targetPos[0]) / 2.0,
            targetPos[1] + (targetDest[1] - targetPos[1]) / 2.0)
        halfway_eta = calculate_time_to_dest(position, halfway_point, speed)
        target_halfway_eta = calculate_time_to_dest(target_start_point,
            halfway_point, targetSpeed)
        if abs(halfway_eta - target_halfway_eta) < 0.005:
            return halfway_point
        elif halfway_eta < target_halfway_eta:
            targetDest = halfway_point
        elif halfway_eta >= target_halfway_eta:
            targetPos = halfway_point
    return halfway_point


class Point(object):
    def __init__(self, x, y, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return "Point(%s, %s)" % (self.x, self.y)

    def __eq__(self, rhs):
        return rhs and rhs.x == self.x and rhs.y == self.y and rhs.z == rhs.z

    def tuple(self):
        return (self.x, self.y)


class Path(object):
    def __init__(self, points=[], speed=0.0):
        self.path = []
        self.speed = speed
        if points:
            self.set_path(points)

    def time_to_move(self, point1, point2, speed):
        return distance(point1.x, point1.y, point2.x, point2.y) / speed

    def set_path(self, points):
        self.path = []
        last_point = points[0]
        current_time = _get_now()
        self.path.append( (last_point, current_time ) )
        for point in points[1:]:
            current_time += self.time_to_move(last_point, point, self.speed)
            self.path.append( (point, current_time ) )
            last_point = point

    def __repr__(self):
        return "Path(%s)" % ([p for p in self.path],)

    def plot_intercept_point_from(self, point, speed):
        path_position = (self.x(), self.y())
        intercept = plot_intercept_point(point.tuple(), speed, path_position,
            self.path[-1][0].tuple(), self.speed)
        return Point(*intercept)

    def match_path_from(self, point, speed):
        if not self.path:
            return []
        path = list(self.path)
        while path[1:]:
            (start, starttime), (end, endtime) = path[:2]
            if self.time_to_move(point, end, speed) < endtime:
                intercept = self.plot_intercept_point_from(point, speed)
                newpath = Path()
                newpath.path.append((intercept, self.time_to_move(point,
                    intercept, speed)))
                newpath.path.extend([p for p in path[1:]])
                return newpath
            path.pop(0)

        return Path()

    def position(self):
        return Point(self.x(), self.y())

    def x(self):
        now = _get_now()
        path = list(self.path)
        start, millis = path[0]
        while path and now > millis:
            start, millis = path.pop(0)
        if not path:
            return self.path[-1].x
        (start_x, start_y), start_time = start.tuple(), millis
        end_point, end_time = path[0]
        end_x, end_y = end_point.tuple()

        if now > end_time:
            return end_x
        diff_x = end_x - start_x
        diff_t = end_time - start_time
        if diff_t <= 0:
            return end_x
        inc = (now - start_time) / diff_t
        return start_x + diff_x * inc

    def y(self):
        now = _get_now()
        path = list(self.path)
        start, millis = path[0]
        while path and now > millis:
            start, millis = path.pop(0)
        if not path:
            return self.path[-1].y
        (start_x, start_y), start_time = start.tuple(), millis
        end_point, end_time = path[0]
        end_x, end_y = end_point.tuple()

        if now > end_time:
            return end_y
        diff_y = end_y - start_y
        diff_t = end_time - start_time
        if diff_t <= 0:
            return end_y
        inc = (now - start_time) / diff_t
        return start_y + diff_y * inc


