
import json

from gevent.queue import Queue
from rooms.views import jsonview
from rooms.timer import Timer

import logging
log = logging.getLogger("rooms.player_connection")


class PlayerConnection(object):
    def __init__(self, game_id, username, room, actor, token):
        self.game_id = game_id
        self.username = username
        self.room = room
        self.actor = actor
        self.token = token
        self.queues = []

    def __repr__(self):
        return "<PlayerConnection %s in %s-%s>" % (self.username,
            self.game_id, self.room.room_id)

    def new_queue(self):
        queue = Queue()
        self.queues.append(queue)
        return queue

    def send_message(self, message):
        log.debug("PlayerConnection: sending message to %s queues: %s",
            len(self.queues), message)
        for queue in self.queues:
            queue.put(message)

    def redirect(self, node_host, node_port, token):
        self.send_message({"command": "redirect",
            "node": [node_host, node_port], "token": token})

    def redirect_to_master(self, master_host, master_port):
        self.send_message({"command": "redirect_to_master",
            "master": [master_host, master_port]})

    def actor_update(self, actor):
        self.send_message({"command": "actor_update",
            "actor_id": actor.actor_id, "data": jsonview(actor)})

    def remove_actor(self, actor):
        self.send_message({"command": "remove_actor",
            "actor_id": actor.actor_id})

    def send_sync(self, room):
        self.send_message({"command": "sync", "data": {"now": Timer.now(),
            "username": self.username, "room_id": room.room_id}})

    def send_sync_to_websocket(self, ws, room, username):
        ws.send(json.dumps(self._sync_message(room, username)))
        for actor in room.actors.values():
            ws.send(json.dumps(
                {"command": "actor_update", "actor_id": actor.actor_id,
                "data": jsonview(actor)}))

    def _sync_message(self, room, username):
        return {"command": "sync", "data": {"now": Timer.now(),
            "username": username, "room_id": room.room_id}}
