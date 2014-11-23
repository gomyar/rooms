
from rooms.position import Position
from gevent.queue import Queue
from rooms.views import jsonview
from rooms.timer import Timer
from rooms.player_connection import command_update
from rooms.player_connection import command_remove

import logging
log = logging.getLogger("rooms.vision")


class Area(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.linked = set()
        self.actors = set()
        self.actor_queues = set()

    def __eq__(self, rhs):
        return rhs and type(rhs) is Area and rhs.x == self.x and \
            rhs.y == self.y

    def __repr__(self):
        return "<%s %s, %s>" % (self.__class__.__name__, self.x, self.y)

NullArea = Area(-1, -1)

class GridVision(object):
    def __init__(self, room, gridsize=10, linksize=1):
        self.room = room
        self.areas = dict()
        self.gridsize = gridsize
        self.linksize = linksize
        self._create_areas()

        # actor_id => area
        self.actor_map = dict()
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

    def add_actor(self, actor):
        area = self.area_at(actor.vector.start_pos)
        area.actors.add(actor)
        self.actor_map[actor.actor_id] = area
        for link in area.linked:
            for actor_id in link.actor_queues:
                for queue in self.actor_queues[actor_id]:
                    queue.put(command_update(actor))
        # sync connected queues
        if actor.actor_id in self.actor_queues:
            area.actor_queues.add(actor.actor_id)
            for queue in self.actor_queues[actor.actor_id]:
                self._send_sync_to_queue(actor, queue)

    def actor_update(self, actor):
        area = self.area_for_actor(actor)
        for link in area.linked:
            for actor_id in link.actor_queues:
                for queue in self.actor_queues[actor_id]:
                    queue.put(command_update(actor))

    def _send_command(self, actor_id, command):
        for queue in self.actor_queues[actor_id]:
            queue.put(command)

    def actor_removed(self, actor):
        area = self.area_for_actor(actor)
        area.actors.remove(actor)
        self.actor_map.pop(actor.actor_id)
        for link in area.linked:
            for actor_id in link.actor_queues:
                self._send_command(actor_id, command_remove(actor))
        if actor.actor_id in self.actor_queues:
            for actor.actor_id in self.actor_queues[actor.actor_id]:
                area = self.area_for_actor(actor)
                if actor_id in area.actor_queues:
                    area.actor_queues.remove(actor_id)

    def actor_state_changed(self, actor):
        area = self.area_for_actor(actor)
        for link in area.linked:
            for actor_id in link.actor_queues:
                self._send_command(actor_id, command_update(actor))

    def actor_vector_changed(self, actor, previous):
        current_area = self.actor_map[actor.actor_id]
        new_area = self.area_at(actor.vector.start_pos)
        if current_area == new_area:
            # area has not changed, propagate event as normal
            for link in current_area.linked:
                for actor_id in link.actor_queues:
                    self._send_command(actor_id, command_update(actor))
        else:
            # area changed
            self.actor_map[actor.actor_id] = new_area
            current_area.actors.remove(actor)
            new_area.actors.add(actor)

            removed_areas = current_area.linked.difference(new_area.linked)
            added_areas = new_area.linked.difference(current_area.linked)
            same_areas = new_area.linked.intersection(current_area.linked)

            # actor changed area events
            for area in removed_areas:
                for actor_id in area.actor_queues:
                    if actor_id != actor.actor_id:
                        self._send_command(actor_id, command_remove(actor))
            for area in added_areas:
                for actor_id in area.actor_queues:
                    if actor_id != actor.actor_id:
                        self._send_command(actor_id, command_update(actor))
            for area in same_areas:
                for actor_id in area.actor_queues:
                    if actor_id != actor.actor_id:
                        self._send_command(actor_id, command_update(actor))

            # Listener changed area events
            if actor.actor_id in self.actor_queues:
                current_area.actor_queues.remove(actor.actor_id)
                new_area.actor_queues.add(actor.actor_id)
                for queue in self.actor_queues[actor.actor_id]:
                    for area in removed_areas:
                        for a in area.actors:
                            if a.actor_id != actor.actor_id:
                                queue.put(command_remove(a))
                    for area in added_areas:
                        for a in area.actors:
                            if a.actor_id != actor.actor_id:
                                queue.put(command_update(a))
                self._send_command(actor.actor_id, command_update(actor))

    def actor_becomes_invisible(self, actor):
        log.debug("actor_becomes_invisible")
        area = self.area_for_actor(actor)
        for link in area.linked:
            for actor_id in link.actor_queues:
                for queue in self.actor_queues[actor_id]:
                    queue.put(command_remove(actor))

    def actor_becomes_visible(self, actor):
        log.debug("actor_becomes_visible")
        area = self.area_for_actor(actor)
        for link in area.linked:
            for actor_id in link.actor_queues:
                self._send_command(actor_id, command_update(actor))

    def area_for_actor(self, actor):
        return self.actor_map.get(actor.actor_id, NullArea)

    def send_all_visible_actors(self, listener):
        for area in self.area_for_actor(listener.actor).linked:
            for actor in area.actors:
                listener.actor_update(actor)

    def connect_vision_queue(self, actor_id):
        queue = Queue()
        if actor_id not in self.actor_queues:
            self.actor_queues[actor_id] = []
        self.actor_queues[actor_id].append(queue)
        if actor_id in self.room.actors:
            actor = self.room.actors[actor_id]
            self._send_sync_to_queue(actor, queue)
            area = self.area_at(actor.vector.start_pos)
            area.actor_queues.add(actor_id)
            self.actor_map[actor_id] = area
        return queue

    def disconnect_vision_queue(self, actor_id, queue):
        self.actor_queues[actor_id].remove(queue)
        if not self.actor_queues[actor_id]:
            self.actor_queues.pop(actor_id)
            if actor_id in self.room.actors:
                actor = self.room.actors[actor_id]
                area = self.area_for_actor(actor)
                area.actor_queues.remove(actor_id)

    def _send_sync_to_queue(self, actor, queue):
        queue.put(self._sync_message(actor))
        for area in self.area_for_actor(actor).linked:
            for a in area.actors:
                queue.put(command_update(a))

    def _sync_message(self, actor):
        return {"command": "sync", "data": {"now": Timer.now(),
            "username": actor.username, "room_id": self.room.room_id,
            "player_actor": jsonview(actor)}}
