
import math


class Position(object):
    def __init__(self, x, y, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __repr__(self):
        if self.z != 0:
            return "<Pos %s,%s,%s>" % (self.x, self.y, self.z)
        else:
            return "<Pos %s,%s>" % (self.x, self.y)

    def __eq__(self, rhs):
        return rhs and type(rhs) is Position and self.x == rhs.x and \
            self.y == rhs.y and self.z == rhs.z

    def distance_to(self, position):
        width = self.x - position.x
        height = self.y - position.y
        depth = self.z - position.z
        return math.sqrt(math.pow(width, 2) + math.pow(height, 2) + \
            math.pow(depth, 2))
