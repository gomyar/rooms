
from rooms.position import Position


class Area(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.linked = set()
        self.listeners = set()
        self.actors = set()

    def __eq__(self, rhs):
        return rhs and type(rhs) is Area and rhs.x == self.x and \
            rhs.y == self.y

    def __repr__(self):
        return "<Area %s, %s>" % (self.x, self.y)


class GridVision(object):
    def __init__(self, room, gridsize=10):
        self.room = room
        self.areas = dict()
        self.gridsize = gridsize
        self._create_areas()

        self.actor_map = dict()

    def _create_areas(self):
        for y in range(0, int(self.room.height / self.gridsize)):
            for x in range(0, int(self.room.width / self.gridsize)):
                self.areas[x, y] = Area(x, y)
        for area in self.areas.values():
            area.linked = set([self.areas.get((area.x + x, area.y + y)) for \
                y in range(-1, 2) for x in range(-1, 2) if \
                self.areas.get((area.x + x, area.y + y))])

    def area_at(self, position):
        x = int(position.x) / self.gridsize
        y = int(position.y) / self.gridsize
        return self.areas.get((x, y))

    def add_listener(self, listener):
        area = self.area_for_actor(listener.actor)
        area.listeners.add(listener)

    def actor_update(self, actor):
        area = self.area_for_actor(actor)
        for link in area.linked:
            for listener in link.listeners:
                listener.actor_update(actor)

    def actor_removed(self, actor):
        area = self.area_for_actor(actor)
        area.actors.remove(actor)
        for link in area.linked:
            for listener in link.listeners:
                listener.actor_removed(actor)

    def actor_state_changed(self, actor):
        area = self.area_for_actor(actor)
        for link in area.linked:
            for listener in link.listeners:
                listener.actor_state_changed(actor)

    def actor_vector_changed(self, actor, previous):
        area = self.area_for_actor(actor)
        for link in area.linked:
            for listener in link.listeners:
                listener.actor_vector_changed(actor, previous)

    def actor_becomes_invisible(self, actor):
        area = self.area_for_actor(actor)
        for link in area.linked:
            for listener in link.listeners:
                listener.actor_becomes_invisible(actor)

    def actor_becomes_visible(self, actor):
        area = self.area_for_actor(actor)
        for link in area.linked:
            for listener in link.listeners:
                listener.actor_becomes_visible(actor)

    def area_for_actor(self, actor):
        if actor not in self.actor_map:
            self.actor_map[actor] = self.area_at(actor.vector.start_pos)
            self.actor_map[actor].actors.add(actor)
        return self.actor_map[actor]
