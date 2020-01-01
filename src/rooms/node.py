
import gevent
import json
from geventwebsocket import WebSocketError

from rooms.actor import Actor
from rooms.scriptset import ScriptSet
from rooms.room_loader import RoomLoader
from rooms.node_updater import NodeUpdater
from rooms.views import jsonview
from rooms.player_connection import command_redirect
from rooms.player_connection import AdminConnection

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


class Node(object):
    def __init__(self, container, name, host):
        self.container = container
        self.name = name
        self.rooms = dict()
        self.scripts = ScriptSet()
        self.node_updater = NodeUpdater(self)
        self.room_loader = RoomLoader(self)
        self.host = host
        self.load = 0.0
        self.players = dict()

        self._nodeupdater_gthread = None
        self._roomload_gthread = None
        self.active = False

    def start(self):
        log.info("Starting node %s at %s", self.name, self.host)
        self.disassociate_rooms()
        self.node_updater.send_onlinenode_update()
        self.start_node_update()
        self.start_room_loader()
        self.active = True
        log.info("Started node %s at %s", self.name, self.host)

    def disassociate_rooms(self):
        self.container.disassociate_rooms(self.name)

    def load_scripts(self, script_path):
        self.scripts.load_scripts(script_path)

    def start_node_update(self):
        self.node_updater.start()

    def start_room_loader(self):
        self.room_loader.start()

    def load_next_pending_room(self):
        room = self.container.load_next_pending_room(self.name)
        if room:
            room.node = self
            self.rooms[room.game_id, room.room_id] = room
            if not room.initialized:
                room.script.call("room_created", room)
                room.initialized = True
                self.container.update_room(room, initialized=True)
            else:
                self.container.load_actors_for_room(room)
            room.start()

    def save_actor_to_other_room(self, exit_room_id, actor, exit_position=None):
        actor._game_id = actor.game_id
        if exit_position:
            actor.position = exit_position
        actor._room_id = exit_room_id
        actor.room = None
        self.container.save_actor(actor, limbo=True) # (, async=False) ?
        if actor.is_player:
            self.players[actor.game_id, actor.username] = exit_room_id, actor.actor_id

    def player_connects(self, ws, game_id, username):
        if (game_id, username) not in self.players:
            log.warning("No room for player: %s, %s",
                game_id, username)
            return

        room_id, actor_id = self.players[game_id, username]
        room = self.rooms[game_id, room_id]
        queue = room.vision.connect_vision_queue(actor_id)

        try:
            connected = True
            while connected:
                message = queue.get()
                if message.get("command") == 'disconnect':
                    connected = False
                    ws.send(json.dumps(jsonview(message)))
                elif message.get("command") == 'move_room':
                    log.debug("Moving room for %s to %s", username,
                        message['room_id'])
                    room.vision.disconnect_vision_queue(actor_id, queue)
                    if (game_id, message['room_id']) in self.rooms:
                        log.debug("Room already managed: %s",
                            message['room_id'])
                        ws.send(json.dumps(jsonview(message)))
                        room = self.rooms[game_id, message['room_id']]
                        queue = room.vision.connect_vision_queue(
                            actor_id)
                    else:
                        log.debug("Redirecting to master")
                        ws.send(json.dumps({'command': 'redirect_to_master'}))
                else:
                    ws.send(json.dumps(jsonview(message)))
        except WebSocketError as wse:
            log.debug("Websocket socket dead: %s", str(wse))
        except Exception as e:
            log.exception("Unexpected exception in player connection")
            raise
        finally:
            room.vision.disconnect_vision_queue(actor_id, queue)

    def shutdown(self):
        self.active = False
        # stop all gthreads
        self.room_loader.stop()
        self.node_updater.stop()

        for room in self.rooms.values():
            room.stop()

        # send disconnect to player queues
        for room in self.rooms.values():
            for queues in room.vision.actor_queues.values():
                for queue in queues:
                    queue.put({'command': 'disconnect'})

        # save actors - wait for actor save queue to end

        # deactivate rooms
        for room in self.rooms.values():
            self.container.save_room(room, blank_node_name=True)

    def admin_connects(self, ws, game_id, room_id):
        room = self.rooms[game_id, room_id]
        queue = room.vision.connect_admin_queue()
        admin_conn = AdminConnection(game_id, room_id, None)
        admin_conn.send_sync_to_websocket(ws, room, "admin")
        try:
            connected = True
            while connected:
                message = queue.get()
                ws.send(json.dumps(jsonview(message)))
                if message.get("command") in ['disconnect', 'redirect']:
                    connected = False
        except WebSocketError as wse:
            log.debug("Admin Websocket socket dead: %s", str(wse))
        except Exception as e:
            log.exception("Unexpected exception in player connection")
            raise
        finally:
            room.vision.disconnect_admin_queue(queue)

    def actor_call(self, game_id, username, actor_id, method, **kwargs):
        if (game_id, username) not in self.players:
            log.warning("No room for player: %s, %s",
                game_id, username)
            raise Exception("No room for player: %s, %s" % (
                game_id, username))

        room_id, actor_id = self.players[game_id, username]
        room = self.rooms[game_id, room_id]
        actor = room.actors[actor_id]

        if actor.username != username:
            log.debug("Cannot call method on actor %s for user %s", actor_id, username)
            raise Exception("Cannot Call actor")

        log.debug("Calling %s, %s -> %s", room_id, actor_id, method)

        return actor.script_call(method, **kwargs)
