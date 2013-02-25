
from collections import defaultdict


class VisibilityGrid(object):
    def __init__(self, width, height, gridsize=10):
        self.width = width
        self.height = height
        self.gridsize = gridsize
        self.registered = defaultdict(lambda: set())
        self.actors = defaultdict(lambda: set())

    def add_actor(self, actor, x, y, distance):
        if actor in self.actors:
            self.remove_actor(actor)
        self.actors[actor] = set()
        for grid_pos in self._gridpoints(x, y, distance):
            if grid_pos not in self.registered:
                self.registered[grid_pos] = set()
            self.registered[grid_pos].add(actor)
            self.actors[actor].add(grid_pos)

    def add_actor(self, actor, x, y, distance):
        gridpoints = self.actors.get(actor, set())
        newgridpoints = set(self._gridpoints(x, y, distance))
        removed_gridpoints = gridpoints.difference(newgridpoints)
        added_gridpoints = newgridpoints.difference(gridpoints)

        added_actors = set()
        for grid_point in added_gridpoints:
            self.registered[grid_point].add(actor)
            for listener in self.registered[grid_point]:
                if self.actors[listener].intersection(newgridpoints):
                    if listener != actor:
                        added_actors.add(listener)
        for listener in added_actors:
            listener.actor_added(actor)

        removed_actors = set()
        for grid_point in removed_gridpoints:
            self.registered[grid_point].remove(actor)
            for listener in self.registered[grid_point]:
                if not self.actors[listener].intersection(gridpoints):
                    if listener != actor:
                        removed_actors.add(listener)
        for listener in removed_actors:
            listener.actor_removed(actor)

        area_actors = set()
        for grid_point in newgridpoints:
            for target in self.registered[grid_point]:
                if self.actors[listener].intersection(newgridpoints):
                    if target != actor:
                        area_actors.add(target)
            self.registered[grid_point].add(actor)
        for target in area_actors:
            actor.actor_added(target)
        self.actors[actor] = newgridpoints




    def add_actor(self, actor, x, y, distance):
        gridpoints = self.actors.get(actor, set())
        newgridpoints = set(self._gridpoints(x, y, distance))

        actors = set()
        for grid_point in gridpoints:
            actors.update(self.registered[grid_point])
        newactors = set()
        for grid_point in newgridpoints:
            newactors.update(self.registered[grid_point])

        added_actors = newactors.difference(actors)
        removed_actors = actors.difference(newactors)

        for added in added_actors:
            if added != actor:
                actor.actor_added(added)
                added.actor_added(actor)

        for removed in removed_actors:
            if removed != actor:
                actor.actor_removed(removed)
                removed.actor_removed(actor)

        removed_gridpoints = gridpoints.difference(newgridpoints)
        added_gridpoints = newgridpoints.difference(gridpoints)

        for grid_point in added_gridpoints:
            self.registered[grid_point].add(actor)

        for grid_point in removed_gridpoints:
            self.registered[grid_point].remove(actor)

        self.actors[actor] = newgridpoints



    def remove_actor(self, actor):
        for grid_point in self.actors[actor]:
            self.registered[grid_point].remove(actor)
        self.actors.pop(actor)

    def update_actor(self, actor, x, y, distance):
#        newgridpoints = set(self._gridpoints(x, y, distance))
#        gridpoints = self.actors[actor]
#        removed_actors = set()
#        for grid_point in gridpoints:
#            if grid_point not in newgridpoints:
#                for target in self.registered[grid_point]:
#                    removed_actors.add(target)
#        for target in removed_actors:
#            target.actor_removed(actor)
        self.add_actor(actor, x, y, distance)

    def _gridpoints(self, x, y, distance):
        x1, y1 = (x - distance, y - distance)
        x1, y1 = (x1 / self.gridsize, y1 / self.gridsize)
        x2, y2 = (x + distance, y + distance)
        x2, y2 = (x2 / self.gridsize + 1,
            y2 / self.gridsize + 1)
        for ry in range(max(0, y1), min(self.width / self.gridsize, y2)):
            for rx in range(max(0, x1), min(self.height / self.gridsize, x2)):
                yield (rx, ry)

    def _registered_actors(self, position):
        return self.registered.get((position[0] / self.gridsize,
            position[1] / self.gridsize), [])

    def left_grid(self, actor, position):
        for actor in self._registered_actors(position):
            actor._update("remove_actor", actor.actor_id)

    def entered_grid(self, actor, position):
        for actor in self._registered_actors(position):
            actor._update("actor_update", actor.external())

    def actor_added(self, actor, x, y):
        for target in self._registered_actors((x, y)):
            target.actor_added(actor)

    def actor_removed(self, actor, x, y):
        pass

    # actor_update
