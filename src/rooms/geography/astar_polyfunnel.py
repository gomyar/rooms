
import pointformatting

_connected_offsets = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1)
]


class Point(object):
    def __init__(self, polygon):
        self.polygon = polygon
        self.parent = None
        self._f = 0
        self._g = 0
        self._h = 0
        self._connected = None

    def __eq__(self, rhs):
        return rhs and self.polygon == rhs.polygon

    def __repr__(self):
        return "Point(%s)" % (self.polygon)

    def connected(self):
        if self._connected is None:
            self._connected = []
            for connection in self.polygon.connections:
                self._connected.append(Point(connection.target_polygon))
        return self._connected

    def calc_g(self):
        if self.parent:
            self._g = self.polygon.distance_to(self.parent.polygon)
        else:
            self._g = 0

    def calc_h(self, target_point):
        self._h = self.polygon.distance_to(target_point.polygon)

    def calc_f(self):
        self._f = self._g + self._h

    def f(self):
        return self._f

    def recalc_points(self, target_point):
        self.calc_h(target_point)
        self.calc_f()
        self.calc_g()


class AStar(object):
    def __init__(self, geography):
        self.geography = geography
        self.point_map = {}
        self.open_list = []
        self.closed_list = []

    def _lowest_f_point(self):
        return min(self.open_list, key=Point.f)

    def find_path(self, from_position, to_position):
        self.open_list = []
        self.closed_list = []

        from_poly = self.geography.find_poly_at_point(from_position)
        to_poly = self.geography.get_poly_at_point(to_position)
        if not from_poly or not to_poly:
            return []

        from_point = Point(from_poly)
        to_point = Point(to_poly)

        self.open_list.append(Point(from_poly))

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
        # open list is empty (no path) (extra check for linear paths)
        if not self.open_list and \
                len(self.closed_list) != len(self.geography.polygons):
            return []

        # working backwards from target, using parents, to build path
        path = []
        #current = to_point
        while current.parent and current.parent != from_point:
            path.append(current.parent.polygon)
            current = current.parent

        path.reverse()
        #path.insert(0, from_point.polygon)
        path.append(to_point.polygon)
        return path
