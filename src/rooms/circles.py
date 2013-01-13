
class Circles(object):
    def __init__(self):
        self.circle_id = ""
        self.circles = dict()

    def is_allied(self, actor):
        return self.circle_id == actor.circles.circle_id

    def is_friendly(self, actor):
        return self.circles.get(actor.circles.circle_id, 0) > 0

    def is_neutral(self, actor):
        return self.circles.get(actor.circles.circle_id, 0) == 0

    def is_enemy(self, actor):
        return self.circles.get(actor.circles.circle_id, 0) < 0
