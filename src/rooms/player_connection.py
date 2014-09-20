
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
        if actor.visible:
            self.send_message({"command": "actor_update",
                "actor_id": actor.actor_id, "data": jsonview(actor)})

    def actor_removed(self, actor):
        if actor.visible:
            self.send_message({"command": "remove_actor",
                "actor_id": actor.actor_id})

    def actor_becomes_visible(self, actor):
        self.actor_update(actor)

    def actor_becomes_invisible(self, actor):
        self.actor_removed(actor)

    def send_sync(self, room):
        self.send_message(self._sync_message(room))

    def send_sync_to_websocket(self, ws, room, username):
        ws.send(json.dumps(self._sync_message(room)))
        for actor in room.actors.values():
            if actor.visible:
                ws.send(json.dumps({"command": "actor_update",
                    "actor_id": actor.actor_id, "data": jsonview(actor)}))

    def _sync_message(self, room):
        return {"command": "sync", "data": {"now": Timer.now(),
            "username": self.username, "room_id": room.room_id}}


class AdminConnection(PlayerConnection):
    def actor_becomes_invisible(self, actor):
        self.actor_update(actor)

    def _sync_message(self, room):
        sync_msg = super(AdminConnection, self)._sync_message(room)
        sync_msg['map_url'] = "http://mapurl"
        return sync_msg
