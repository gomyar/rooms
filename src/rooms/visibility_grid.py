
from collections import defaultdict

import logging
log = logging.getLogger("rooms.visibility")


class VisibilityGrid(object):
    def __init__(self, width, height, gridsize=10):
        self.width = width
        self.height = height
        self.gridsize = int(gridsize)
        self.registered = defaultdict(lambda: set())
        self.registered_gridpoints = defaultdict(lambda: set())
        self.actors = dict()
        self.sectors = defaultdict(lambda: set())

    def _register_listener(self, actor):
        log.debug(" ** Registering listener: %s", actor)
        x, y = actor.position()
        distance = actor.vision_distance
        self.registered[actor] = distance
        gridpoints = set(self._gridpoints(x, y, distance))
        self.registered_gridpoints[actor] = gridpoints
        existing = set()
        for grid_point in gridpoints:
            existing.update(self.sectors[grid_point])
            self.sectors[grid_point].add(actor)
        for target in existing:
            actor.actor_added(target)
        self._add_actor(actor)

    def _unregister_listener(self, actor):
        log.debug(" ** Unregistering listener: %s", actor)
        for grid_point in self.registered_gridpoints[actor]:
            self.sectors[grid_point].remove(actor)

    def add_actor(self, actor):
        log.debug(" ** Adding actor: %s", actor)
        if actor.vision_distance:
            self._register_listener(actor)
        else:
            self._add_actor(actor)

    def _add_actor(self, actor):
        x, y = actor.position()
        grid_point = self._gridpoint(x, y)
        self.actors[actor] = grid_point
        self.sectors[grid_point].add(actor)
        self._signal_changed(actor, None, self.actors[actor])

    def update_actor_position(self, actor):
        log.debug(" * update actor position: %s", actor)
        x, y = actor.position()
        old_grid_point = self.actors[actor]
        new_grid_point = self._gridpoint(x, y)
        if old_grid_point != new_grid_point:
            self.sectors[old_grid_point].remove(actor)
            self.sectors[new_grid_point].add(actor)
            self._signal_changed(actor, old_grid_point, new_grid_point)
            if actor in self.registered:
                self._signal_registered_changed(actor, x, y)
        self.actors[actor] = new_grid_point

    def send_update_event(self, actor, update_id, **kwargs):
        grid_point = self.actors[actor]
        for listener in self.sectors[grid_point]:
            listener._update(update_id, **kwargs)

    def send_update_actor(self, actor):
        grid_point = self.actors[actor]
        for listener in self.sectors[grid_point]:
            listener.actor_updated(actor)

    def _signal_changed(self, actor, old_grid_point, new_grid_point):
        old_actors = self.sectors[old_grid_point]
        new_actors = self.sectors[new_grid_point]
        removed_actors = old_actors.difference(new_actors)
        added_actors = new_actors.difference(old_actors)
        for removed in removed_actors:
            if removed in self.registered:
                removed.actor_removed(actor)
        for added in added_actors:
            if added in self.registered:
                added.actor_added(actor)

    def _signal_registered_changed(self, actor, x, y):
        gridpoints = self.registered_gridpoints[actor]
        distance = self.registered[actor]
        newgridpoints = set(self._gridpoints(x, y, distance))

        removed_gridpoints = gridpoints.difference(newgridpoints)
        added_gridpoints = newgridpoints.difference(gridpoints)

        removed_actors = set()
        for grid_point in removed_gridpoints:
            removed_actors.update(self.sectors[grid_point])

        added_actors = set()
        for grid_point in added_gridpoints:
            added_actors.update(self.sectors[grid_point])

        for listener in added_actors:
            if actor != listener:
                actor.actor_added(listener)

        for listener in removed_actors:
            if actor != listener:
                actor.actor_removed(listener)

    def remove_actor(self, actor):
        log.debug(" ** Removing actor; %s", actor)
        if actor in self.registered:
            self._unregister_listener(actor)
        else:
            grid_point = self.actors.pop(actor)
            self.sectors[grid_point].remove(actor)

    def _gridpoint(self, x, y):
        return (int(x) / self.gridsize, int(y) / self.gridsize)

    def _gridpoints(self, x, y, distance):
        x1, y1 = (int(x - distance), int(y - distance))
        x1, y1 = (x1 / self.gridsize, y1 / self.gridsize)
        x2, y2 = (int(x + distance), int(y + distance))
        x2, y2 = (x2 / self.gridsize + 1,
            y2 / self.gridsize + 1)
        for ry in range(max(0, y1), min(self.width / self.gridsize, y2)):
            for rx in range(max(0, x1), min(self.height / self.gridsize, x2)):
                yield (rx, ry)
