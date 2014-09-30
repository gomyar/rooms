

class Area(object):
    def __init__(self, topleft, bottomright):
        self.topleft = topleft
        self.bottomright = bottomright
        self.x1 = min(topleft.x, bottomright.x)
        self.y1 = min(topleft.y, bottomright.y)
        self.x2 = max(topleft.x, bottomright.x)
        self.y2 = max(topleft.y, bottomright.y)

    def __repr__(self):
        return "<Area %s, %s -> %s, %s>" % (self.x1, self.y1, self.x2, self.y2)

    def intersects(self, topleft, bottomright):
        x1 = min(topleft.x, bottomright.x)
        y1 = min(topleft.y, bottomright.y)
        x2 = max(topleft.x, bottomright.x)
        y2 = max(topleft.y, bottomright.y)
        return x1 <= self.x2 and y1 <= self.y2 and \
            x2 >= self.x1 and y2 >= self.y1

    def actor_in(self, actor):
        return self.intersects(actor.vector.start_pos, actor.vector.end_pos)

    def vector_in(self, vector):
        return self.intersects(vector.start_pos, vector.end_pos)


class Visibility(object):
    def __init__(self):
        self.visible_areas = dict()
        self.listeners = set()

    def add_visible_area(self, topleft, bottomright):
        self.visible_areas[topleft, bottomright] = Area(topleft, bottomright)

    def add_listener(self, listener):
        self.listeners.add(listener)

    def actor_update(self, actor):
        for listener in self._get_listeners_for_areas(self._find_areas(actor)):
            listener.actor_update(actor)

    def actor_removed(self, actor):
        for listener in self._get_listeners_for_areas(self._find_areas(actor)):
            listener.actor_removed(actor)

    def actor_state_changed(self, actor):
        for listener in self._get_listeners_for_areas(self._find_areas(actor)):
            listener.actor_state_changed(actor)

    def actor_vector_changed(self, actor, previous_vector):
        for listener in self._get_listeners_for_areas(self._find_areas(actor)):
            listener.actor_vector_changed(actor, previous_vector)

    def actor_becomes_visible(self, actor):
        for listener in self._get_listeners_for_areas(self._find_areas(actor)):
            listener.actor_becomes_visible(actor)

    def actor_becomes_invisible(self, actor):
        for listener in self._get_listeners_for_areas(self._find_areas(actor)):
            listener.actor_becomes_invisible(actor)

    def actor_vector_changed(self, actor, previous_vector):
        # get all areas for current vector
        current_areas = set(self._find_areas(actor))
        # get all areas for previous vector
        previous_areas = set(self._find_areas_by_vector(previous_vector))
        # get areas which have been removed
        removed = previous_areas.difference(current_areas)
        # send remove to removed listeners
        for listener in self._get_listeners_for_areas(removed):
            # get all areas for listener
            listener_areas = set(self._find_areas(listener.actor))
            if not listener_areas.intersection(current_areas):
                listener.actor_removed(actor)
        # send update to added listeners
        for listener in self._get_listeners_for_areas(current_areas):
            listener.actor_vector_changed(actor, previous_vector)

    def _find_areas(self, actor):
        for area in self.visible_areas.values():
            if area.actor_in(actor):
                yield area

    def _find_areas_by_vector(self, vector):
        for area in self.visible_areas.values():
            if area.vector_in(vector):
                yield area

    def _get_listeners_for_areas(self, area_iter):
        listeners = set()
        for area in area_iter:
            for listener in self.listeners:
                if area.actor_in(listener.actor):
                    listeners.add(listener)
        return listeners
