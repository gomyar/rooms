
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
        self._connected = []

    def __eq__(self, rhs):
        return rhs and type(rhs) is Point and \
            rhs.x == self.x and rhs.y == self.y and \
            rhs.passable == self.passable

    def __repr__(self):
        return "<Point %s, %s>" % (self.x, self.y)

    def connected(self):
        return self._connected

    def hook_up_connected(self, point_spacing=1):
        self._connected = list(self._find_connected(point_spacing))

    def _find_connected(self, point_spacing=1):
        connected = []
        for offset in _connected_offsets:
            point = ((offset[0]) * point_spacing + self.x,
                (offset[1]) * point_spacing + self.y)
            if self.point_map[point] and self.point_map[point].passable:
                connected.append(self.point_map[point])
        return connected

    def connected_points(self):
        return [(point.x, point.y) for point in self.connected()]

    def unhook_connected(self, point_spacing=1):
        connected = []
        for offset in _connected_offsets:
            point = ((offset[0]) * point_spacing + self.x,
                (offset[1]) * point_spacing + self.y)
            if self.point_map[point] and \
                    self in self.point_map[point]._connected:
                connected.append(self.point_map[point])
        for point in connected:
            point._connected.remove(self)
            if point.parent == self:
                point.parent = None
                point._f = 0
                point._g = 0
                point._h = 0
        self._connected = []

    def calc_g(self):
        if self.parent:
            diff_x = self.parent.x - self.x
            diff_y = self.parent.y - self.y
            if diff_x and diff_y:
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
    def __init__(self, width, height, point_spacing=1):
        self._points = dict()
        self.width = 0
        self.height = 0
        self.point_spacing = point_spacing
        for x in range(0, width, point_spacing):
            for y in range(0, height, point_spacing):
                point = Point(x, y)
                self._points[x, y] = point
                point.point_map = self
                self.width = max(self.width, x + point_spacing)
                self.height = max(self.height, y + point_spacing)
        for x in range(0, width, point_spacing):
            for y in range(0, height, point_spacing):
                point = self[x, y]
                point.hook_up_connected(point_spacing)

    def __getitem__(self, key):
        return self._points.get(key)

    def make_impassable(self, from_key, to_key=None):
        to_key = to_key or from_key
        for x in range(from_key[0], to_key[0] + 1, self.point_spacing):
            for y in range(from_key[1], to_key[1] + 1, self.point_spacing):
                if (x, y) in self._points:
                    self._points[x, y].passable = False
                    self._points[x, y].unhook_connected(self.point_spacing)

class AStar(object):
    def __init__(self, point_map):
        self.point_map = point_map
        self.open_list = []
        self.closed_list = []

    def _lowest_f_point(self):
        return min(self.open_list, key=Point.f)

    def find_path(self, from_point, to_point):
        self.open_list = []
        self.closed_list = []
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
