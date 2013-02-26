
from collections import defaultdict


class VisibilityGrid(object):
    def __init__(self, width, height, gridsize=10):
        self.width = width
        self.height = height
        self.gridsize = gridsize
        self.registered = defaultdict(lambda: set())
        self.registered_gridpoints = defaultdict(lambda: set())
        self.actors = defaultdict(lambda: set())
        self.sectors = defaultdict(lambda: set())

    def register_listener(self, actor, x, y, distance):
        self.registered[actor] = distance
        gridpoints = set(self._gridpoints(x, y, distance))
        self.registered_gridpoints[actor] = gridpoints
        existing = set()
        for grid_point in gridpoints:
            existing.update(self.sectors[grid_point])
            self.sectors[grid_point].add(actor)
        for target in existing:
            actor.actor_added(target)
        self.add_actor(actor, x, y)

    def unregister_listener(self, actor):
        distance = self.registered.pop(actor)
        for grid_point in self._gridpoints(x, y, distance):
            self.sectors[grid_point].remove(actor)
        self.remove_actor(actor)

    def add_actor(self, actor, x, y):
        grid_point = self._gridpoint(x, y)
        self.actors[actor] = grid_point
        self.sectors[grid_point].add(actor)
        self._signal_changed(actor, None, self.actors[actor])

    def update_actor(self, actor, x, y):
        old_grid_point = self.actors[actor]
        new_grid_point = self._gridpoint(x, y)
        if old_grid_point != new_grid_point:
            self.sectors[old_grid_point].remove(actor)
            self.sectors[new_grid_point].add(actor)
            self._signal_changed(actor, old_grid_point, new_grid_point)
            if actor in self.registered:
                self._signal_registered_changed(actor, x, y)
        self.actors[actor] = new_grid_point

    def _signal_changed(self, actor, old_grid_point, new_grid_point):
        old_actors = self.sectors[old_grid_point]
        new_actors = self.sectors[new_grid_point]
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
        grid_point = self.actors.pop(actor)
        self.sectors[grid_point].remove(actor)

    def _gridpoint(self, x, y):
        return (x / self.gridsize, y / self.gridsize)

    def _gridpoints(self, x, y, distance):
        x1, y1 = (x - distance, y - distance)
        x1, y1 = (x1 / self.gridsize, y1 / self.gridsize)
        x2, y2 = (x + distance, y + distance)
        x2, y2 = (x2 / self.gridsize + 1,
            y2 / self.gridsize + 1)
        for ry in range(max(0, y1), min(self.width / self.gridsize, y2)):
            for rx in range(max(0, x1), min(self.height / self.gridsize, x2)):
                yield (rx, ry)
