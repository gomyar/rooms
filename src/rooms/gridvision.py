
from rooms.position import Position
from gevent.queue import Queue

import logging
log = logging.getLogger("rooms.vision")


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

NullArea = Area(0, 0)

class GridVision(object):
    def __init__(self, room, gridsize=10, linksize=1):
        self.room = room
        self.areas = dict()
        self.gridsize = gridsize
        self.linksize = linksize
        self._create_areas()

        # actor => area
        self.actor_map = dict()
        # actor => listener
        self.listener_actors = dict()

        # actor_id => queue
        self.actor_queues = dict()

    def _create_areas(self):
        for y in range(0, int(self.room.height / self.gridsize) + 1):
            for x in range(0, int(self.room.width / self.gridsize) + 1):
                self.areas[x, y] = Area(x, y)
        for area in self.areas.values():
            area.linked = set([self.areas.get((area.x + x, area.y + y)) for \
                y in range(-self.linksize, self.linksize + 1) for \
                x in range(-self.linksize, self.linksize + 1) if \
                self.areas.get((area.x + x, area.y + y))])

    def area_at(self, position):
        x = int((position.x - self.room.topleft.x) / self.gridsize)
        y = int((position.y - self.room.topleft.y) / self.gridsize)
        return self.areas.get((x, y))

    def add_listener(self, listener):
        area = self.area_for_actor(listener.actor)
        area.listeners.add(listener)
        self.listener_actors[listener.actor] = listener

    def remove_listener(self, listener):
        area = self.area_for_actor(listener.actor)
        area.listeners.remove(listener)
        self.listener_actors.pop(listener.actor)

    def add_actor(self, actor):
        area = self.area_at(actor.vector.start_pos)
        area.actors.add(actor)
        self.actor_map[actor] = area
        for link in area.linked:
            for listener in link.listeners:
                listener.actor_update(actor)

    def actor_update(self, actor):
        area = self.area_for_actor(actor)
        for link in area.linked:
            for listener in link.listeners:
                listener.actor_update(actor)

    def actor_removed(self, actor):
        area = self.area_for_actor(actor)
        area.actors.remove(actor)
        self.actor_map.pop(actor)
        for link in area.linked:
            for listener in link.listeners:
                listener.actor_removed(actor)

    def actor_state_changed(self, actor):
        area = self.area_for_actor(actor)
        for link in area.linked:
            for listener in link.listeners:
                listener.actor_state_changed(actor)

    def actor_vector_changed(self, actor, previous):
        current_area = self.actor_map[actor]
        new_area = self.area_at(actor.vector.start_pos)
        if current_area == new_area:
            # area has not changed, propagate event as normal
            for link in current_area.linked:
                for listener in link.listeners:
                    listener.actor_vector_changed(actor, previous)
        else:
            # area changed
            self.actor_map[actor] = new_area
            current_area.actors.remove(actor)
            new_area.actors.add(actor)

            removed_areas = current_area.linked.difference(new_area.linked)
            added_areas = new_area.linked.difference(current_area.linked)
            same_areas = new_area.linked.intersection(current_area.linked)

            # actor changed area events
            for area in removed_areas:
                for listener in area.listeners:
                    if listener.actor != actor:
                        listener.actor_removed(actor)
            for area in added_areas:
                for listener in area.listeners:
                    if listener.actor != actor:
                        listener.actor_update(actor)
            for area in same_areas:
                for listener in area.listeners:
                    if listener.actor != actor:
                        listener.actor_vector_changed(actor, previous)

            # Listener changed area events
            if actor in self.listener_actors:
                listener = self.listener_actors[actor]
                current_area.listeners.remove(listener)
                new_area.listeners.add(listener)
                for area in removed_areas:
                    for actor in area.actors:
                        if listener.actor != actor:
                            listener.actor_removed(actor)
                for area in added_areas:
                    for actor in area.actors:
                        if listener.actor != actor:
                            listener.actor_update(actor)
                listener.actor_vector_changed(listener.actor, previous)

    def actor_becomes_invisible(self, actor):
        log.debug("actor_becomes_invisible")
        area = self.area_for_actor(actor)
        for link in area.linked:
            for listener in link.listeners:
                listener.actor_becomes_invisible(actor)

    def actor_becomes_visible(self, actor):
        log.debug("actor_becomes_visible")
        area = self.area_for_actor(actor)
        for link in area.linked:
            for listener in link.listeners:
                listener.actor_becomes_visible(actor)

    def area_for_actor(self, actor):
        return self.actor_map.get(actor, NullArea)

    def send_sync(self, listener):
        listener.send_sync(self.room)
        self.send_all_visible_actors(listener)

    def send_all_visible_actors(self, listener):
        for area in self.area_for_actor(listener.actor).linked:
            for actor in area.actors:
                listener.actor_update(actor)

    def connect_vision_queue(self, actor_id):
        queue = Queue()
        if actor_id not in self.actor_queues:
            self.actor_queues[actor_id] = []
        self.actor_queues[actor_id].append(queue)
        return queue
