
from .astar import PointMap
from .astar import AStar
from rooms.position import Position


class PointmapGeography(object):
    def __init__(self, point_spacing=10):
        self.point_spacing = point_spacing
        self._pointmaps = dict()

    def draw(self):
        return {"type": "pointmap", "polygons": []}

    def _get_pointmap(self, room):
        if room not in self._pointmaps:
            pm_width = int(room.width / self.point_spacing) * self.point_spacing
            pm_height = int(room.height / self.point_spacing) * self.point_spacing
            pm_width_2 = int((room.width / 2) / self.point_spacing) * self.point_spacing
            pm_height_2 = int((room.height / 2) / self.point_spacing) * self.point_spacing
            pointmap = PointMap()
            pointmap.init_square_points(
                -pm_width_2,
                -pm_height_2,
                pm_width,
                pm_height,
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
        start = (int(start.x / self.point_spacing) * self.point_spacing,
            int(start.y / self.point_spacing) * self.point_spacing)
        end = (int(end.x / self.point_spacing) * self.point_spacing,
            int(end.y / self.point_spacing) * self.point_spacing)
        if not pointmap[end] or not pointmap[end].passable:
            end = self.get_available_position_closest_to(room, end)
        if not pointmap[start] or not pointmap[start].passable:
            start = self.get_available_position_closest_to(room, start)
        path = AStar(pointmap).find_path(pointmap[start], pointmap[end])
        path.insert(0, start)
        return [Position(*point) for point in path]

    def setup(self, room):
        pass
