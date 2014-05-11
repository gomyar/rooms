
from rooms.timer import Timer


def create_vector(start_pos, end_pos, speed=1):
    start_time = Timer.now()
    end_time = time_to_position(start_pos, end_pos, speed)
    return Vector(start_pos, start_time, end_pos, end_time)


def time_to_position(start_pos, end_pos, speed):
    return start_pos.distance_to(end_pos) / speed


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
