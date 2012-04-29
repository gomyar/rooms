
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

    def on_horizontal(self, y):
        return self.y2 > y and self.y1 < y

    def subdivide_horizontal(self, y):
        return [Rect(self.x1, self.y1, self.x2, y), Rect(self.x1, y,
            self.x2, self.y2)]

    def overlaps(self, rect):
        return (self.x1 < rect.x2 and self.y1 < rect.y2 and \
                self.x2 > rect.x1 and self.y2 > rect.y1)

    def on_vertical(self, x):
        return self.x2 > x and self.x1 < x

    def subdivide_vertical(self, x):
        return [Rect(self.x1, self.y1, x, self.y2), Rect(x, self.y1,
            self.x2, self.y2)]

    def external(self):
        return (self.x1, self.y1, self.x2, self.y2)

    def edges(self):
        return (self.x1, self.y1, self.x2, self.y2)

    def lengthof(self, start, end):
        return math.hypot(end[0] - start[0], end[1] - start[1])

    def _intersect_vertical(self, x1, y1, x2, y2, x):
        w = x2 - x1
        h = y2 - y1
        l = math.hypot(w, h)
        ww = x - x1
        return y1 + (h * ww / w)

    def _intersect_horizontal(self, x1, y1, x2, y2, y):
        w = x2 - x1
        h = y2 - y1
        l = math.hypot(w, h)
        hh = y - y1
        return x1 + (w * hh / h)

    def line_intersects_rect(self, line):
        start, end = line
        x1, y1 = start
        x2, y2 = end
        left, top, right, bottom = self.edges()

        if x2 > right:
            y2 = self._intersect_vertical(x1, y1, x2, y2, right)
            x2 = right

        if x2 < left:
            y2 = self._intersect_vertical(x1, y1, x2, y2, left)
            x2 = left

        if y2 > bottom:
            x2 = self._intersect_horizontal(x1, y1, x2, y2, bottom)
            y2 = bottom

        if y2 < top:
            x2 = self._intersect_horizontal(x1, y1, x2, y2, top)
            y2 = top

        return x2, y2


class BasicRectGeography:
    def get_path(self, room, start, end):
        return [ start, end ]


    def subdivide(self, room):
        rects = [Rect(*room.wall_positions())]
        for room_obj in room.map_objects:
            topRects = [r for r in rects if r.on_horizontal(room_obj.top())]
            for r in topRects:
                rects.extend(r.subdivide_horizontal(room_obj.top()))
                rects.remove(r)
            bottomRects = [r for r in rects if r.on_horizontal(
                room_obj.bottom())]
            for r in bottomRects:
                rects.extend(r.subdivide_horizontal(room_obj.bottom()))
                rects.remove(r)

            leftRects = [r for r in rects if r.on_vertical(room_obj.left())]
            for r in leftRects:
                rects.extend(r.subdivide_vertical(room_obj.left()))
                rects.remove(r)
            rightRects = [r for r in rects if r.on_vertical(
                room_obj.right())]
            for r in rightRects:
                rects.extend(r.subdivide_vertical(room_obj.right()))
                rects.remove(r)
        for room_obj in room.map_objects:
            for rect in list(rects):
                if rect.overlaps(Rect(*room_obj.wall_positions())):
                    rects.remove(rect)
        return rects
