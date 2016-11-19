
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

from rooms.rpc import request
from rooms.rpc import websocket

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


class NodeController(object):
    def __init__(self, node):
        self.node = node

    @websocket
    def player_connects(self, ws, token):
        return self.node.player_connects(ws, token)

    @websocket
    def admin_connects(self, ws, token):
        return self.node.admin_connects(ws, token)

    @request
    def actor_call(self, game_id, token, method, **kwargs):
        return self.node.actor_call(game_id, token, method, **kwargs)

    @request
    def actor_request(self, game_id, token, actor_id, method, **kwargs):
        return self.node.actor_request(game_id, token, actor_id, method,
            **kwargs)


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

        self._nodeupdater_gthread = None
        self._roomload_gthread = None

    def start(self):
        self.disassociate_rooms()
        self.start_node_update()
        self.start_room_loader()

    def disassociate_rooms(self):
        self.container.disassociate_rooms(self.name)

    def load_scripts(self, script_path):
        self.scripts.load_scripts(script_path)

    def start_node_update(self):
        self._nodeupdater_gthread = gevent.spawn(self.node_updater.update_loop)

    def start_room_loader(self):
        self._roomload_gthread = gevent.spawn(self.room_loader.load_loop)

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
            room.start()

    def save_actor_to_other_room(self, exit_room_id, exit_position, actor):
        actor._game_id = actor.game_id
        actor.position = exit_position
        actor._room_id = exit_room_id
        actor.room = None
        self.container.save_actor(actor, limbo=True) # (, async=False) ?
        if actor.is_player and (actor.game_id, exit_room_id) not in self.rooms:
            conn = self.player_connections.pop((actor.username, actor.game_id))
            self.connections.pop(conn.token)
            log.debug("Removed conn: %s", conn)

    def player_connects(self, ws, token):
        # validate stored token first, if invalid, do this:
        player_conn = self.container.get_player_for_token(token)

        if player_conn is None:
            raise Exception("Unauthorized")

        game_id = player_conn['game_id']
        username = player_conn['username']

        if (game_id, player_conn['room_id']) not in self.rooms:
            log.warning("No room for player: %s, %s",
                game_id, player_conn['room_id'])
            raise Exception("No room for player: %s, %s" % (
                game_id, player_conn['room_id']))

        room = self.rooms[game_id, player_conn['room_id']]
        queue = room.vision.connect_vision_queue(player_conn['actor_id'])

        try:
            connected = True
            while connected:
                message = queue.get()
                if message.get("command") == 'disconnect':
                    connected = False
                    ws.send(json.dumps(jsonview(message)))
                elif message.get("command") == 'move_room':
                    log.debug("Moving room for %s to %s", player_conn['username'],
                        message['room_id'])
                    if (game_id, message['room_id']) in self.rooms:
                        log.debug("Room already managed: %s",
                            message['room_id'])
                        room = self.rooms[game_id, message['room_id']]
                        ws.send(json.dumps(jsonview(message)))
                        queue = room.vision.connect_vision_queue(
                            player_conn['actor_id'])
                    else:
                        log.debug("Redirecting to master")
                        ws.send(json.dumps({'command': 'redirect_to_master'}))
                else:
                    ws.send(json.dumps(jsonview(message)))
        except WebSocketError, wse:
            log.debug("Websocket socket dead: %s", str(wse))
        except Exception, e:
            log.exception("Unexpected exception in player connection")
            raise
        finally:
            room.vision.disconnect_vision_queue(player_conn['actor_id'], queue)

    def shutdown(self):
        # stop all gthreads
        self.room_loader.running = False
        self.node_updater.running = False

        if self._roomload_gthread:
            self._roomload_gthread.join()
        if self._nodeupdater_gthread:
            self._nodeupdater_gthread.join()

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
            self.container.save_room(room)

    def admin_connects(self, ws, token):
        admin_token = self.container.get_admin_token(token)

        if admin_token is None:
            raise Exception("Unauthorized")

        log.debug("Admin conects: %s", token)
        room = self.rooms[admin_token.game_id, admin_token.room_id]
        queue = room.vision.connect_admin_queue()
        admin_conn = AdminConnection(admin_token.game_id, admin_token.room_id,
                                     admin_token.token)
        admin_conn.send_sync_to_websocket(ws, room, "admin")
        try:
            connected = True
            while connected:
                message = queue.get()
                ws.send(json.dumps(jsonview(message)))
                if message.get("command") in ['disconnect', 'redirect']:
                    connected = False
        except WebSocketError, wse:
            log.debug("Admin Websocket socket dead: %s", str(wse))
        except Exception, e:
            log.exception("Unexpected exception in player connection")
            raise
        finally:
            room.vision.disconnect_admin_queue(queue)
