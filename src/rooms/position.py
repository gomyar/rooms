
import math


class Position(object):
    def __init__(self, x, y, z=0):
        self.x, self.y, self.z = float(x), float(y), float(z)

    def __repr__(self):
        if self.z != 0:
            return "<Pos %s,%s,%s>" % (self.x, self.y, self.z)
        else:
            return "<Pos %s,%s>" % (self.x, self.y)

    def __eq__(self, rhs):
        return rhs and type(rhs) is Position and self.x == rhs.x and \
            self.y == rhs.y and self.z == rhs.z

    def coords(self):
        return (self.x, self.y) if not self.z else (self.x, self.y, self.z)

    def distance_to(self, position):
        width = self.x - position.x
        height = self.y - position.y
        depth = self.z - position.z
        return math.sqrt(math.pow(width, 2) + math.pow(height, 2) + \
            math.pow(depth, 2))

    def add_coords(self, x, y, z=0):
        return Position(self.x + x, self.y + y, self.z + z)

    def is_within(self, topleft, bottomright):
        x, y, z = self.x, self.y, self.z
        return x >= topleft.x and x <= bottomright.x and \
            y >= topleft.y and y <= bottomright.y and \
            z >= topleft.z and z <= bottomright.z

    def offset_position(self, distance, yaw):
        x = self.x + distance * math.cos(yaw)
        y = self.y + distance * math.sin(yaw)
        return Position(x, y)

