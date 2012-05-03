
import math


class Rect:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def __repr__(self):
        return "<Rect %s, %s, %s, %s>" % (self.x1, self.y1, self.x2, self.y2)

    def __eq__(self, rhs):
        return rhs and rhs.x1 == self.x1 and rhs.y1 == self.y1 and \
            rhs.x2 == self.x2 and rhs.x2 == self.x2


class RectCollection:
    def __init__(self, rect_width=10, rect_height=10):
        self.rects = dict()
        self.rect_width = rect_width
        self.rect_height = rect_height

    def rect_at(self, x, y):
        return self.rects.get((x, y))

    def add_rect(self, x, y, rect):
        self.rects[(x, y)] = rect

    def __getitem__(self, position):
        x, y = position[0], position[1]
        x = position[0] / self.rect_width
        y = position[1] / self.rect_height
        return self.rect_at(x, y)

    def __len__(self):
        return len(self.rects)


class BasicSquareGeography:
    def __init__(self, rect_width=10, rect_height=10):
        self.rect_width = rect_width
        self.rect_height = rect_height
        self.rooms = dict()

    def _subdivide(self, room):
        rects = RectCollection(self.rect_width, self.rect_height)
        for x in range(0, room.width, self.rect_width):
            for y in range(0, room.height, self.rect_height):
                if not room.object_at(x, y):
                    rects.add_rect(x / self.rect_width, y / self.rect_height, \
                        Rect(x + room.position[0], y + room.position[1],
                            self.rect_width, self.rect_height))
        return rects

    def _get_rects_for(self, room):
        if room not in self.rooms:
            self.rooms[room] = self._subdivide(room)
        return self.rooms[room]

    def get_path(self, room, start, end):
        # get line to end
        w = (end[0] - start[0])
        h = (end[1] - start[1])
        slope = h / w if w else h
        length = math.hypot(w, h)
        x_hop = w * 10 / length
        y_hop = h * 10 / length

        # walk line, if endpoint found, start from last good point
        path = [start]
        rects = self._get_rects_for(room)
        point = start
        next_point = (int(point[0] + x_hop), int(point[1] + y_hop))
        index = 0
        while rects[next_point] and index < length / 10:
            point = next_point
            next_point = (int(point[0] + x_hop), int(point[1] + y_hop))
            index += 1
            path.append(point)

        # try to walk to adjacent square, if none, return path

        # repeat
        if len(path) > 1:
            return path
        else:
            return [path[0], point]
