
from rooms.timer import Timer
from rooms.position import Position


def create_vector(start_pos, end_pos, speed=1):
    start_time = Timer.now()
    end_time = start_time + time_to_position(start_pos, end_pos, speed)
    return Vector(start_pos, start_time, end_pos, end_time)

def create_vector_list(path, speed):
    vectors = []
    time = Timer.now()
    for i in range(len(path) - 1):
        end_time = time + time_to_position(path[i], path[i + 1], speed)
        vectors.append(Vector(path[i], time, path[i + 1], end_time))
        time = end_time
    return vectors


def build_vector(x1, y1, x2, y2, speed=1):
    return create_vector(Position(x1, y1), Position(x2, y2), speed)


def time_to_position(start_pos, end_pos, speed):
    return start_pos.distance_to(end_pos) / speed


def time_to(path, speed):
    current = path[0]
    total = 0
    for point in path[1:]:
        total += time_to_position(current, point, speed)
        current = point
    return total


class Vector(object):
    def __init__(self, start_pos, start_time, end_pos, end_time):
        self.start_pos = start_pos
        self.start_time = start_time
        self.end_pos = end_pos
        self.end_time = end_time

    def __repr__(self):
        return "<Vector %s at %s -> %s at %s>" % (self.start_pos,
            self.start_time, self.end_pos, self.end_time)

    def __eq__(self, rhs):
        return rhs and type(rhs) is Vector and \
            self.start_pos == rhs.start_pos and \
            self.end_pos == rhs.end_pos and \
            self.start_time == rhs.start_time and \
            self.end_time == rhs.end_time

    def _calc_d(self, start_d, end_d):
        now = Timer.now()
        if now > self.end_time:
            return end_d
        diff_x = end_d - start_d
        diff_t = self.end_time - self.start_time
        if diff_t <= 0:
            return end_d
        inc = (now - self.start_time) / diff_t
        return start_d + diff_x * inc

    @property
    def x(self):
        return self._calc_d(self.start_pos.x, self.end_pos.x)

    @property
    def y(self):
        return self._calc_d(self.start_pos.y, self.end_pos.y)

    @property
    def z(self):
        return self._calc_d(self.start_pos.z, self.end_pos.z)

    def position(self):
        return Position(self.x, self.y, self.z)

    def time_to_destination(self):
        return self.end_time - Timer.now()

    def yaw(self):
        return self.start_pos.angle_between(self.end_pos)

    def extrapolate(self, ratio=1.0):
        x, y, z = self.x, self.y, self.z
        tx, ty, tz = self.end_pos.x, self.end_pos.y, self.end_pos.z
        return Position(
            x + (tx - x) * ratio,
            y + (ty - y) * ratio,
            z + (tz - z) * ratio)
