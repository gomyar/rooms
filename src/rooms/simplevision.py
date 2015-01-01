
from gevent.queue import Queue
from rooms.timer import Timer
from rooms.views import jsonview
from rooms.player_connection import command_update
from rooms.player_connection import command_remove


class Vision(object):
    def __init__(self, room):
        self.room = room
        self.actor_queues = dict()
        self.admin_queues = set()

    def add_actor(self, actor):
        if actor.actor_id in self.actor_queues:
            self._send_sync_for_actor(actor)
            self._admin_update(actor)
        else:
            self.actor_update(actor)

    def _send_sync_for_actor(self, actor):
        if actor.actor_id in self.actor_queues:
            for queue in self.actor_queues[actor.actor_id]:
                self._send_sync_to_queue(actor, queue)

    def actor_update(self, actor):
        if actor.visible:
            for actor_id in self.actor_queues:
                self._send_update(actor_id, actor)
        elif actor.actor_id in self.actor_queues:
            self._send_update(actor.actor_id, actor)
        elif actor.parent_id in self.actor_queues:
            self._send_update(actor.parent_id, actor)
        self._admin_update(actor)

    def _send_update(self, actor_id, actor):
        self._send_command(actor_id, command_update(actor))

    def _send_remove(self, actor_id, actor):
        self._send_command(actor_id, command_remove(actor))

    def _send_command(self, actor_id, command):
        for queue in self.actor_queues[actor_id]:
            queue.put(command)

    def actor_removed(self, actor):
        if actor.visible:
            for actor_id in self.actor_queues:
                self._send_remove(actor_id, actor)
        elif actor.actor_id in self.actor_queues:
            self._send_remove(actor.actor_id, actor)
        elif actor.parent_id in self.actor_queues:
            self._send_remove(actor.parent_id, actor)
        self._admin_remove(actor)

    def actor_state_changed(self, actor):
        self.actor_update(actor)

    def actor_vector_changed(self, actor):
        self.actor_update(actor)

    def actor_becomes_invisible(self, actor):
        for actor_id in self.actor_queues:
            if actor.actor_id == actor_id:
                self._send_update(actor_id, actor)
            elif actor.parent_id == actor_id:
                self._send_update(actor_id, actor)
            else:
                self._send_remove(actor_id, actor)
        self._admin_update(actor)

    def actor_becomes_visible(self, actor):
        self.actor_update(actor)

    def area_for_actor(self, actor):
        return self.actor_map.get(actor.actor_id, NullArea)

    def connect_vision_queue(self, actor_id):
        queue = Queue()
        if actor_id not in self.actor_queues:
            self.actor_queues[actor_id] = []
        self.actor_queues[actor_id].append(queue)
        if actor_id in self.room.actors:
            actor = self.room.actors[actor_id]
            self._send_sync_to_queue(actor, queue)
        return queue

    def disconnect_vision_queue(self, actor_id, queue):
        self.actor_queues[actor_id].remove(queue)
        if not self.actor_queues[actor_id]:
            self.actor_queues.pop(actor_id)

    def _send_sync_to_queue(self, actor, queue):
        queue.put(self._sync_message(actor))
        for a in self.room.actors.values():
            if a.visible or a.actor_id == actor.actor_id or \
                    a.parent_id == actor.actor_id:
                queue.put(command_update(a))

    def _sync_message(self, actor):
        return {"command": "sync", "data": {"now": Timer.now(),
            "username": actor.username, "room_id": self.room.room_id,
            "player_actor": jsonview(actor)}}

    def connect_admin_queue(self):
        queue = Queue()
        self.admin_queues.add(queue)
        for actor in self.room.actors.values():
            self._admin_update(actor)
        return queue

    def disconnect_admin_queue(self, queue):
        self.admin_queues.remove(queue)

    def _admin_update(self, actor):
        for queue in self.admin_queues:
            queue.put(command_update(actor))

    def _admin_remove(self, actor):
        for queue in self.admin_queues:
            queue.put(command_remove(actor))

    def send_message(self, message_type, position, data):
        message = dict(command="message", message_type=message_type,
            position=jsonview(position), data=data)
        for actor_id in self.actor_queues:
            for queue in self.actor_queues[actor_id]:
                queue.put(message)
