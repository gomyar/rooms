
from collections import defaultdict

import logging
log = logging.getLogger("rooms.visibility")


class VisibilityGrid(object):
    def __init__(self, width, height, gridsize=10):
        self.width = width
        self.height = height
        self.gridsize = int(gridsize)
        self.registered = defaultdict(lambda: 0)
        self.registered_gridpoints = defaultdict(lambda: set())
        self.actors = dict()
        self.sectors = defaultdict(lambda: set())
        self.registered_sectors = defaultdict(lambda: set())

    def visible_actors(self, actor):
        gridpoints = self.registered_gridpoints[actor]
        actors = set()
        for gridpoint in gridpoints:
            actors.update(self.sectors[gridpoint])
        return actors

    def register_listener(self, actor):
        log.debug(" ** Registering listener: %s", actor)
        x, y = actor.position()
        distance = actor.vision_distance
        self.registered[actor] = distance
        gridpoints = set(self._gridpoints(x, y, distance))
        self.registered_gridpoints[actor] = gridpoints
        existing = set()
        for grid_point in gridpoints:
            existing.update(self.sectors[grid_point])
            self.registered_sectors[grid_point].add(actor)
        for target in existing:
            if target != actor:
                actor.actor_added(target)

    def unregister_listener(self, actor):
        log.debug(" ** Unregistering listener: %s", actor)
        removing = set()
        for grid_point in self.registered_gridpoints[actor]:
            removing.update(self.sectors[grid_point])
            self.registered_sectors[grid_point].remove(actor)
        for target in removing:
            if target != actor:
                actor.actor_removed(target)
        self.registered.pop(actor)
        self.registered_gridpoints.pop(actor)

    def _remove_actor(self, actor):
        grid_point = self.actors.pop(actor)
        self.sectors[grid_point].remove(actor)
        self._signal_changed(actor, grid_point, None)

    def add_actor(self, actor):
        log.debug(" ** Adding actor: %s", actor)
        x, y = actor.position()
        grid_point = self._gridpoint(x, y)
        self.actors[actor] = grid_point
        self.sectors[grid_point].add(actor)
        self._signal_changed(actor, None, self.actors[actor])

    def update_actor_position(self, actor):
        log.debug(" * update actor position: %s", actor)
        if actor in self.actors:
            x, y = actor.position()
            old_grid_point = self.actors[actor]
            new_grid_point = self._gridpoint(x, y)
            if old_grid_point != new_grid_point:
                log.debug("signal changed %s", actor)
                self._signal_changed(actor, old_grid_point, new_grid_point)
                self.sectors[old_grid_point].remove(actor)
                self.sectors[new_grid_point].add(actor)
                self.actors[actor] = new_grid_point
        if actor in self.registered:
            log.debug("registered changed")
            self._signal_registered_changed(actor, x, y)

    def send_update_event(self, actor, update_id, **kwargs):
        if actor in self.actors:
            grid_point = self.actors[actor]
            for listener in self.registered_sectors[grid_point]:
                listener._update(update_id, **kwargs)

    def send_update_actor(self, actor):
        if actor in self.actors:
            grid_point = self.actors[actor]
            for listener in self.registered_sectors[grid_point]:
                listener.actor_updated(actor)

    def _signal_changed(self, actor, old_grid_point, new_grid_point):
        old_actors = self.registered_sectors[old_grid_point]
        new_actors = self.registered_sectors[new_grid_point]
        removed_actors = old_actors.difference(new_actors)
        added_actors = new_actors.difference(old_actors)
        for removed in removed_actors:
            if removed != actor:
                removed.actor_removed(actor)
        for added in added_actors:
            if added != actor:
                added.actor_added(actor)

    def _signal_registered_changed(self, actor, x, y):
        gridpoints = self.registered_gridpoints[actor]
        newgridpoints = set(self._gridpoints(x, y, actor.vision_distance))

        removed_gridpoints = gridpoints.difference(newgridpoints)
        added_gridpoints = newgridpoints.difference(gridpoints)

        removed_actors = set()
        for grid_point in removed_gridpoints:
            self.registered_sectors[grid_point].remove(actor)
            removed_actors.update(self.sectors[grid_point])

        added_actors = set()
        for grid_point in added_gridpoints:
            self.registered_sectors[grid_point].add(actor)
            added_actors.update(self.sectors[grid_point])

        for listener in added_actors:
            if actor != listener and self._gridpoint(*listener.position()) not in gridpoints:
                actor.actor_added(listener)

        for listener in removed_actors:
            if actor != listener and self._gridpoint(*listener.position()) not in newgridpoints:
                actor.actor_removed(listener)

        self.registered_gridpoints[actor] = newgridpoints

    def remove_actor(self, actor):
        log.debug(" ** Removing actor; %s", actor)
        self._remove_actor(actor)

    def _gridpoint(self, x, y):
        return (int(x) / self.gridsize, int(y) / self.gridsize)

    def _gridpoints(self, x, y, distance):
        if not distance:
            return []
        x1, y1 = (int(x - distance), int(y - distance))
        x1, y1 = (x1 / self.gridsize, y1 / self.gridsize)
        x2, y2 = (int(x + distance), int(y + distance))
        x2, y2 = (x2 / self.gridsize + 1,
            y2 / self.gridsize + 1)
        points = []
        for ry in range(max(0, y1), min(self.height / self.gridsize, y2)):
            for rx in range(max(0, x1), min(self.width / self.gridsize, x2)):
                points.append((rx, ry))
        return points

    def _actor_sectors(self, actor):
        return set([gridpoint for gridpoint in self.sectors if \
            actor in self.sectors[gridpoint]])

    def vision_distance_changed(self, actor):
        if actor.vision_distance and actor not in self.registered:
            self.register_listener(actor)
        elif not actor.vision_distance and actor in self.registered:
            self.unregister_listener(actor)
        else:
            self._signal_registered_changed(actor, *actor.position())
