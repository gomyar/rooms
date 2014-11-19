
import json

from gevent.queue import Queue
from rooms.views import jsonview
from rooms.timer import Timer

import logging
log = logging.getLogger("rooms.player_connection")


def command_update(actor):
    return {"command": "actor_update",
        "actor_id": actor.actor_id, "data": jsonview(actor)}


def command_remove(actor):
    return {"command": "remove_actor", "actor_id": actor.actor_id}


def command_redirect(host, port):
    return {"command": "redirect_to_master",
            "master": [host, port]}


class PlayerConnection(object):
    def __init__(self, game_id, username, room, actor_id, token):
        self.game_id = game_id
        self.username = username
        self.actor_id = actor_id
        self.token = token
        self.queues = []

    def __repr__(self):
        return "<PlayerConnection %s in %s-%s>" % (self.username,
            self.game_id, self.room.room_id)

    @property
    def room(self):
        return self.actor.room

    def new_queue(self):
        queue = Queue()
        self.queues.append(queue)
        return queue

    def send_message(self, message):
        for queue in self.queues:
            queue.put(message)

    def redirect(self, node_host, node_port, token):
        self.send_message({"command": "redirect",
            "node": [node_host, node_port], "token": token})

    def redirect_to_master(self, master_host, master_port):
        self.send_message(command_redirect(master_host, master_port))

    def actor_update(self, actor):
        if actor.visible:
            self.send_message(command_update(actor))

    def actor_removed(self, actor):
        if actor.visible:
            self.send_message({"command": "remove_actor",
                "actor_id": actor.actor_id})

    def actor_state_changed(self, actor):
        self.actor_update(actor)

    def actor_vector_changed(self, actor, previous_vector):
        self.actor_update(actor)

    def actor_becomes_visible(self, actor):
        self.actor_update(actor)

    def actor_becomes_invisible(self, actor):
        self.actor_removed(actor)

    def send_sync(self, room):
        self.send_message(self._sync_message(room))

    def _sync_message(self, room):
        return {"command": "sync", "data": {"now": Timer.now(),
            "username": self.username, "room_id": room.room_id,
            "player_actor": jsonview(self.actor)}}


class AdminConnection(PlayerConnection):
    def __init__(self, game_id, room, token):
        self.game_id = game_id
        self._room = room
        self.token = token
        self.queues = []

    @property
    def room(self):
        return self._room

    def actor_becomes_invisible(self, actor):
        self.actor_update(actor)

    def send_sync_to_websocket(self, ws, room, username):
        ws.send(json.dumps(self._sync_message(room)))
        for actor in room.actors.values():
            ws.send(json.dumps(command_update(actor)))

    def _sync_message(self, room):
        sync_msg = super(AdminConnection, self)._sync_message(room)
        sync_msg['map_url'] = "http://mapurl"
        sync_msg['data']['vision'] = {"gridsize": self.room.vision.gridsize}
        return sync_msg

    def actor_update(self, actor):
        self.send_message(command_update(actor))

    def actor_removed(self, actor):
        self.send_message(command_remove(actor))
