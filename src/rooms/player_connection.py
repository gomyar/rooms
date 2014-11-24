
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
    def __init__(self, game_id, username, room_id, actor_id, token):
        self.game_id = game_id
        self.username = username
        self.actor_id = actor_id
        self.room_id = room_id
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
        self.token = token
        self.queues = []
        self.username = "admin"

    def send_sync_to_websocket(self, ws, room, username):
        ws.send(json.dumps(self._sync_message(room)))
        for actor in room.actors.values():
            ws.send(json.dumps(command_update(actor)))

    def _sync_message(self, room):
        sync_msg = {"command": "sync", "data": {"now": Timer.now(),
             "username": "admin", "room_id": room.room_id}}
        sync_msg['map_url'] = "http://mapurl"
        sync_msg['data']['vision'] = {"gridsize": room.vision.gridsize}
        return sync_msg

    def actor_update(self, actor):
        self.send_message(command_update(actor))

    def actor_removed(self, actor):
        self.send_message(command_remove(actor))
