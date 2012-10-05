
from astar import PointMap
from astar import AStar


class PointmapGeography(object):
    def __init__(self, point_spacing=10):
        self.point_spacing = point_spacing
        self._pointmaps = dict()

    def _get_pointmap(self, room):
        if room not in self._pointmaps:
            self._pointmaps[room] = PointMap(
                int(room.width / self.point_spacing),
                int(room.height / self.point_spacing))
        return self._pointmaps[room]

    def get_available_position_closest_to(self, room, position):
        pointmap = self._get_pointmap(room)
        return position

    def get_path(self, room, start, end):
        pointmap = self._get_pointmap(room)
        start = start[0] / self.point_spacing, start[1] / self.point_spacing
        end = end[0] / self.point_spacing, end[1] / self.point_spacing
        return AStar(pointmap).find_path(pointmap[start], pointmap[end])
