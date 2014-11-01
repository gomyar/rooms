
from astar import PointMap
from astar import AStar


class PointmapGeography(object):
    def __init__(self, point_spacing=10):
        self.point_spacing = point_spacing
        self._pointmaps = dict()

    def _get_pointmap(self, room):
        if room not in self._pointmaps:
            pointmap = PointMap()
            pointmap.init_square_points(
                int(room.topleft.x),
                int(room.topleft.y),
                int(room.width / self.point_spacing) * self.point_spacing,
                int(room.height / self.point_spacing) * self.point_spacing,
                self.point_spacing)
            for room_object in room.room_objects:
                pointmap.make_impassable(room_object.topleft.coords(),
                    room_object.bottomright.coords())
            self._pointmaps[room] = pointmap
        return self._pointmaps[room]

    def get_available_position_closest_to(self, room, position):
        pointmap = self._get_pointmap(room)
        return min(pointmap.available_points().keys(), key=lambda p: \
            abs(p[0] - position[0]) + abs(p[1] - position[1]))

    def find_path(self, room, start, end):
        pointmap = self._get_pointmap(room)
        start = ((start[0] / self.point_spacing) * self.point_spacing,
            (start[1] / self.point_spacing) * self.point_spacing)
        end = ((end[0] / self.point_spacing) * self.point_spacing,
            (end[1] / self.point_spacing) * self.point_spacing)
        if not pointmap[start]:
            return []
        if not pointmap[end] or not pointmap[end].passable:
            end = self.get_available_position_closest_to(room, end)
        return AStar(pointmap).find_path(pointmap[start], pointmap[end])
