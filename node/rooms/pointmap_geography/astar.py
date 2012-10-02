
import pointformatting

_connected_offsets = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1)
]


class Point(object):
    def __init__(self, x, y, point_map=None):
        self.x = x
        self.y = y
        self.position = (x, y)
        self.point_map = point_map
        self.passable = True
        self.parent = None
        self._f = 0
        self._g = 0
        self._h = 0

    def __eq__(self, rhs):
        return rhs and type(rhs) is Point and \
            rhs.x == self.x and rhs.y == self.y and \
            rhs.passable == self.passable

    def __repr__(self):
        return "<Point %s, %s>" % (self.x, self.y)

    def connected(self):
        for offset in _connected_offsets:
            point = (offset[0] + self.x, offset[1] + self.y)
            if self.point_map[point] and self.point_map[point].passable:
                yield self.point_map[point]

    def connected_points(self):
        return [(point.x, point.y) for point in self.connected()]

    def calc_g(self):
        if self.parent:
            if self.parent.x != self.x and self.parent.y != self.y:
                self._g = 14 + self.parent._g
            else:
                self._g = 10 + self.parent._g
        else:
            self._g = 10

    def calc_h(self, target_point):
        self._h = abs(target_point.x - self.x) * 10 + \
            abs(target_point.y - self.y) * 10

    def calc_f(self):
        self._f = self._g + self._h

    def f(self):
        return self._f

    def recalc_points(self, target_point):
        self.calc_h(target_point)
        self.calc_f()
        self.calc_g()


class PointMap(object):
    def __init__(self, width, height):
        self._points = dict()
        self.width = 0
        self.height = 0
        for x in range(width):
            for y in range(height):
                point = Point(x, y)
                self._points[x, y] = point
                point.point_map = self
                self.width = max(self.width, x + 1)
                self.height = max(self.height, y + 1)

    def __getitem__(self, key):
        return self._points.get(key)

    def make_impassable(self, from_key, to_key=None):
        to_key = to_key or from_key
        for x in range(from_key[0], to_key[0] + 1):
            for y in range(from_key[1], to_key[1] + 1):
                if (x, y) in self._points:
                    self._points[x, y].passable = False

class AStar(object):
    def __init__(self, point_map):
        self.point_map = point_map
        self.open_list = []
        self.closed_list = []

    def _lowest_f_point(self):
        return min(self.open_list, key=Point.f)

    def find_path(self, from_point, to_point):
        # add starting node to open list
        self.open_list.append(from_point)
        # repeat 
        while self.open_list:
            # current point is lowest f-cost point on open list
            current = self._lowest_f_point()
            # switch current point to closed list
            self.open_list.remove(current)
            self.closed_list.append(current)
            # for each connected point
            for connected in current.connected():
                # if not in closed list
                if connected not in self.closed_list:
                    # if not on the open list:
                    if connected not in self.open_list:
                        # add to open list, make current its parent, calc f g h
                        self.open_list.append(connected)
                        connected.parent = current
                        connected.recalc_points(to_point)
                    # else:
                    else:
                        # re-check g cost - if g is lower:
                        if connected._g < current._g:
                            # change points' parent to current, recalc g & f
                            connected.parent = current
                            connected.recalc_points(to_point)
            # break if target point added to closed list
            if to_point in self.closed_list:
                break
        # open list is empty (no path)
        if not self.open_list:
            return []

        # working backwards from target, using parents, to build path
        path = []
        current = to_point
        while current.parent and current.parent != from_point:
            path.append(current.parent.position)
            current = current.parent

        path.reverse()
        path.insert(0, from_point.position)
        path.append(to_point.position)
        return path

    def __repr__(self):
        return pointformatting.format_point(self, self.point_map)
