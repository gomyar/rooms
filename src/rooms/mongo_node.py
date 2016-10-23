
import json
from geventwebsocket import WebSocketError

from rooms.actor import Actor
from rooms.scriptset import ScriptSet
from rooms.actor_loader import ActorLoader
from rooms.views import jsonview

import logging
log = logging.getLogger("rooms.node")


ROOM_LOAD_STATES = ['inactive', 'pending', 'active', 'deactivating']
# Load states:
#   active: room is currently running on a node
#       active = True, pending = N/A, deactivating = False
#   inactive: room is not running on a node nor is it needed
#       active = False, pending = False, deactivating = False
#   pending: room is not running but has been requested
#       active = False, pending = True, deactivating = False
#   deactivating: room is running, has not been requested, is being shut down
#       active = True, pending = N/A, deactivating = True


class Room(object):
    def __init__(self, game_id, room_id):
        self.game_id = game_id
        self.room_id = room_id

        self.active_state = True
        self.pending_state = True
        self.deactivating_state = False


class Player(Actor):
    pass


class Node(object):
    def __init__(self, container, name):
        self.container = container
        self.name = name
        self.rooms = dict()
        self.scripts = ScriptSet()
        self.actor_loader = ActorLoader(self)

    def start(self):
        self.start_actor_loader()

    def start_actor_loader(self):
        loader = ActorLoader(self)
        self._actorload_gthread = gevent.spawn(loader.load_loop)

    def load_next_pending_room(self):
        room = self.container.load_next_pending_room(self.name)
        if room:
            self.rooms[room.game_id, room.room_id] = room
            if not room.initialized:
                room.script.call("room_created", room)
                room.initialized = True
                self.container.save_room(room)
            else:
                self.container.load_actors_for_room(room)
            room.kick()

    def player_connects(self, ws, token):
        player_conn = self.container.get_player_token(token)
        game_id = player_conn['game_id']
        username = player_conn['username']
        room = self.rooms[game_id, player_conn['room_id']]
        queue = room.vision.connect_vision_queue(player_conn['actor_id'])

        try:
            connected = True
            while connected:
                message = queue.get()
                ws.send(json.dumps(jsonview(message)))
                if message.get("command") in ['disconnect', 'redirect']:
                    connected = False
                if message.get("command") == 'move_room':
                    log.debug("Moving room for %s to %s", player_conn['username'],
                        message['room_id'])
                    if (game_id, message['room_id']) in self.rooms:
                        log.debug("Room already managed: %s",
                            message['room_id'])
                        room = self.rooms[game_id, message['room_id']]
                        queue = room.vision.connect_vision_queue(
                            player_conn['actor_id'])
                    else:
                        log.debug("Redirecting to master")
                        ws.send(json.dumps(command_redirect(self.master_host,
                            self.master_port)))
        except WebSocketError, wse:
            log.debug("Websocket socket dead: %s", str(wse))
        except Exception, e:
            log.exception("Unexpected exception in player connection")
            raise
        finally:
            room.vision.disconnect_vision_queue(player_conn['actor_id'], queue)


