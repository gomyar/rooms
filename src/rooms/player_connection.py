
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
    def __init__(self, game_id, username, token, room_id, actor_id,
                 timeout_time=None):
        self.game_id = game_id
        self.username = username
        self.timeout_time = timeout_time
        self.actor_id = actor_id # think this can go
        self.room_id = room_id # think this can go
        self.token = token

    def __repr__(self):
        return "<%s %s in %s-%s>" % (self.__class__.__name__, self.username,
            self.game_id, self.room_id)

    def send_sync(self, room):
        self.send_message(self._sync_message(room))

    def _sync_message(self, room):
        return {"command": "sync", "data": {"now": Timer.now(),
            "username": self.username, "room_id": room.room_id,
            "player_actor": jsonview(self.actor)}}


class AdminConnection(PlayerConnection):
    def __init__(self, game_id, room_id, token):
        self.game_id = game_id
        self.room_id = room_id
        self.queues = []
        self.username = "admin"

    def send_sync_to_websocket(self, ws, room, username):
        ws.send(json.dumps(self._sync_message(room)))
        for actor in room.actors.values():
            ws.send(json.dumps(command_update(actor)))

    def _sync_message(self, room):
        sync_msg = {"command": "sync", "data": {"now": Timer.now(),
             "username": "admin", "room_id": room.room_id},
             "geography": room.geography.draw()}
        sync_msg['map_url'] = "http://mapurl"
        return sync_msg

    def actor_update(self, actor):
        self.send_message(command_update(actor))

    def actor_removed(self, actor):
        self.send_message(command_remove(actor))
