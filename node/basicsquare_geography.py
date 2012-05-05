
import math


class Rect:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.rect_collection = None
        self.position = None

    def __repr__(self):
        return "<Rect %s, %s, %s, %s>" % (self.x1, self.y1, self.x2, self.y2)

    def __eq__(self, rhs):
        return rhs and rhs.x1 == self.x1 and rhs.y1 == self.y1 and \
            rhs.x2 == self.x2 and rhs.x2 == self.x2

    def center(self):
        return (self.x1 + self.x2 / 2, self.y1 + self.y2 / 2)

    def next_rect(self, start, end):
        x_dir = (end[0] - start[0])
        y_dir = (end[1] - start[1])
        rwidth = self.rect_collection.rect_width
        rheight = self.rect_collection.rect_height
        x_dir = int(x_dir / abs(x_dir)) if abs(x_dir) >= rwidth else 0
        y_dir = int(y_dir / abs(y_dir)) if abs(y_dir) >= rheight else 0
        rect = self.rect_collection.rect_at(self.position[0] + x_dir,
            self.position[1])
        if not rect or rect == self:
            rect = self.rect_collection.rect_at(self.position[0],
                self.position[1] + y_dir)
        if rect != self:
            return rect
        else:
            return None


class RectCollection:
    def __init__(self, rect_width=10, rect_height=10):
        self.rects = dict()
        self.rect_width = rect_width
        self.rect_height = rect_height

    def rect_at(self, x, y):
        return self.rects.get((x, y))

    def add_rect(self, x, y, rect):
        self.rects[(x, y)] = rect
        rect.rect_collection = self
        rect.position = (x, y)

    def remove_rect_at(self, x, y):
        rect = self.rects.pop((x, y))
        rect.rect_collection = None

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

    def _line(self, start, end):
        w = (end[0] - start[0])
        h = (end[1] - start[1])
        length = math.hypot(w, h)
        for i, x in enumerate(xrange(0, int(length), int(10))):
            yield (int(start[0] + i * w * 10 / length),
                    int(start[1] + i * h * 10 / length))
        yield end

    def get_path(self, room, start, end):
        rects = self._get_rects_for(room)
        if not rects[start]:
            raise Exception("Invalid start point for path: %s" % (start,))
        line = self._line(start, end)
        point = line.next()
        path = [start]

        while point:
            next_point = line.next()
            if not rects[next_point]:
                path.append(point)
                # try square dirs
                next_rect = rects[point].next_rect(start, end)
                if not next_rect:
                    return path
                else:
                    line = self._line(next_rect.center(), end)
                    point = line.next()
            else:
                point = next_point
        return path
