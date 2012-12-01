
class LinearOpenGeography(object):
    def get_available_position_closest_to(self, room, position):
        return position

    def get_path(self, room, start, end):
        start = (min(max(0, start[0]), room.width),
            min(max(0, start[1]), room.height))
        end = (min(max(0, end[0]), room.width),
            min(max(0, end[1]), room.height))
        return [start, end]

    def intercept(self, path, point, speed):
        return path
