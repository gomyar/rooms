
import uuid
import gevent
import json
import os
from urllib2 import HTTPError

from geventwebsocket import WebSocketError

from rooms.player import PlayerActor
from rooms.rpc import WSGIRPCClient
from rooms.rpc import request
from rooms.rpc import websocket
from rooms.rpc import RPCException
from rooms.rpc import RPCWaitException
from rooms.room import Room
from rooms.script import Script
from rooms.script import NullScript
from rooms.scriptset import ScriptSet
from rooms.views import jsonview
from rooms.timer import Timer
from rooms.player_connection import PlayerConnection
from rooms.player_connection import AdminConnection
from rooms.player_connection import command_redirect
from rooms.actor_loader import ActorLoader

import logging
log = logging.getLogger("rooms.node")


class GameController(object):
    def __init__(self, node):
        self.node = node

    @websocket
    def player_connects(self, ws, game_id, token):
        return self.node.player_connects(ws, game_id, token)

    @request
    def actor_call(self, game_id, token, method, **kwargs):
        return self.node.actor_call(game_id, token, method, **kwargs)

    @request
    def actor_request(self, game_id, token, actor_id, method, **kwargs):
        return self.node.actor_request(game_id, token, actor_id, method,
            **kwargs)

    @websocket
    def admin_connects(self, ws, token):
        return self.node.admin_connects(ws, token)

    @request
    def admin_map(self, token, map_id):
        return self.node.admin_map(token, map_id)


class NodeController(object):
    def __init__(self, node):
        self.node = node

    @request
    def all_rooms(self):
        return self.node.all_rooms()

    @request
    def all_players(self):
        return self.node.all_players()

    @request
    def manage_room(self, game_id, room_id):
        return self.node.manage_room(game_id, room_id)

    @request
    def player_joins(self, username, game_id, room_id, **kwargs):
        return self.node.player_joins(username, game_id, room_id, **kwargs)

    @request
    def request_token(self, username, game_id):
        return self.node.request_token(username, game_id)

    @websocket
    def ping(self, ws):
        return self.node.ping(ws)

    @request
    def deactivate_room(self, game_id, room_id):
        return self.node.deactivate_room(game_id, room_id)

    @request
    def request_admin_token(self, game_id, room_id):
        return self.node.request_admin_token(game_id, room_id)


class Node(object):
    def __init__(self, host, port, master_host, master_port):
        self.host = host
        self.port = port
        self.master_host = master_host
        self.master_port = master_port
        self.rooms = dict()
        self.player_connections = dict()
        self.connections = dict()
        self.admin_connections = dict()
        self.master_conn = WSGIRPCClient(master_host, master_port,
            'master_control')
        self.master_player_conn = WSGIRPCClient(master_host, master_port,
            'master_game')

        self.scripts = ScriptSet()
        self.container = None
        self.room_factory = None
        self._report_gthread = None
        self._actorload_gthread = None

    def load_scripts(self, script_path):
        self.scripts.load_scripts(script_path)

    def connect_to_master(self):
        self.master_conn.call("register_node", host=self.host, port=self.port)

    def start(self):
        self.start_reporting()
        self.start_actor_loader()

    def start_reporting(self):
        self._report_gthread = gevent.spawn(self._start_reporting)

    def _start_reporting(self):
        while True:
            gevent.sleep(5)
            self.master_conn.call("report_load_stats", host=self.host,
                port=self.port, server_load=len(self.rooms) / 100.0,
                node_info=json.dumps(self._compile_node_info()))

    def start_actor_loader(self):
        loader = ActorLoader(self)
        self._actorload_gthread = gevent.spawn(loader.load_loop)

    def _compile_node_info(self):
        node_info = dict()
        for room in self.rooms.values():
            node_info["%s.%s" % (room.game_id, room.room_id)] = dict(
                connected_players=len(self._connected_players_for(room.room_id))
            )
        return node_info

    def _connected_players_for(self, room_id):
        return [conn for conn in self.player_connections.values() if \
            conn.room_id == room_id]

    def deregister(self):
        if self._report_gthread:
            self._report_gthread.kill()
        if self._actorload_gthread:
            self._actorload_gthread.kill()
        self.master_conn.call("offline_node", host=self.host, port=self.port)
        self.save_all()
        self.master_conn.call("deregister_node", host=self.host,
            port=self.port)

    def save_all(self):
        for (game_id, room_id), room in self.rooms.items():
            for actor in room.actors.values():
                actor._kill_gthreads()
                self.container.save_actor(actor)
            self.container.save_room(room)

    def all_rooms(self):
        return [{"game_id": room.game_id, "room_id": room.room_id,
            "actors": [(key, jsonview(a)) for (key, a) in \
            room.actors.items()]} for room in self.rooms.values()]

    def all_players(self):
        return [{"username": conn.username, "game_id": conn.game_id,
            "room_id": conn.room_id, "token": conn.token} for conn in \
            self.player_connections.values()]

    def manage_room(self, game_id, room_id):
        if self.container.room_exists(game_id, room_id):
            room = self.container.load_room(game_id, room_id)
        else:
            room = self.container.create_room(game_id, room_id)
            self.scripts['game_script'].call("room_created", room)
        self.rooms[game_id, room_id] = room
        room.kick()

    def player_joins(self, username, game_id, room_id, **kwargs):
        room = self.rooms[game_id, room_id]
        player_actor = self.container.create_player(room, "player",
            self.scripts['player_script'], username, game_id)
        room.put_actor(player_actor)
        player_conn = self._create_player_conn(username, game_id, room_id,
            player_actor.actor_id)
        self.scripts['player_script'].call("player_joins", player_actor,
            **kwargs)
        return player_conn.token

    def _create_player_conn(self, username, game_id, room_id, actor_id):
        conn_key = username, game_id
        if conn_key not in self.player_connections:
            player_conn = PlayerConnection(game_id, username, room_id,
                actor_id, self._create_token())
            self.player_connections[conn_key] = player_conn
            self.connections[player_conn.token] = player_conn
        return self.player_connections[conn_key]

    def request_token(self, username, game_id):
        log.debug(" **** Requesting token for %s, %s", username, game_id)
        if (username, game_id) not in self.player_connections:
            player_actor = self.container.load_player(username, game_id)
            self._create_player_conn(username, game_id, player_actor.room_id,
                player_actor.actor_id)
        return self.player_connections[username, game_id].token

    def ping(self, ws):
        for i in range(10):
            ws.send(str(i))
            gevent.sleep(1)

    def player_connects(self, ws, game_id, token):
        log.debug("Player connects: %s %s", game_id, token)
        if token not in self.connections:
            raise Exception("Invalid token for player")
        player_conn = self.connections[token]
        room = self.rooms[game_id, player_conn.room_id]
        queue = room.vision.connect_vision_queue(player_conn.actor_id)

        try:
            connected = True
            while connected:
                message = queue.get()
                ws.send(json.dumps(jsonview(message)))
                if message.get("command") in ['disconnect', 'redirect']:
                    connected = False
                if message.get("command") == 'move_room':
                    log.debug("Moving room for %s to %s", player_conn.username,
                        message['room_id'])
                    if (game_id, message['room_id']) in self.rooms:
                        log.debug("Room already managed: %s",
                            message['room_id'])
                        room = self.rooms[game_id, message['room_id']]
                        player_conn = self.connections[token]
                        player_conn.room_id = room.room_id
                        log.debug("Created conn: %s", player_conn)
                        queue = room.vision.connect_vision_queue(
                            player_conn.actor_id)
                    else:
                        log.debug("Redirecting to master")
                        ws.send(json.dumps(command_redirect(self.master_host,
                            self.master_port)))
        except WebSocketError, wse:
            log.debug("Websocket socket dead: %s", str(wse))
        finally:
            room.vision.disconnect_vision_queue(player_conn.actor_id, queue)

    def actor_call(self, game_id, token, method, **kwargs):
        if token not in self.connections:
            raise Exception("Invalid token for player")
        player_conn = self.connections[token]
        room = self.rooms[player_conn.game_id, player_conn.room_id]
        log.debug("call in room: %s - %s: %s(%s)", room.room_id,
            player_conn.token, method, kwargs)
        actor = room.actors[player_conn.actor_id]
        if actor.script.has_method(method):
            actor.script_request(method, actor, **kwargs)
        else:
            raise Exception("No such method %s" % (method,))

    def actor_request(self, game_id, token, actor_id, method, **kwargs):
        if token not in self.connections:
            raise Exception("Invalid token for player")
        player_conn = self.connections[token]
        room = self.rooms[player_conn.game_id, player_conn.room_id]
        actor = room.actors[actor_id]
        log.debug("request in room: %s - %s", room, player_conn)
        player = room.actors[player_conn.actor_id]
        if actor.script.has_method(method):
            return actor.script_request(method, actor, player, **kwargs)
        else:
            raise Exception("No such method %s" % (method,))

    def _create_token(self):
        return str(uuid.uuid1())

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

    def deactivate_room(self, game_id, room_id):
        room = self.rooms.pop((game_id, room_id))
        room.online = False
        for actor in room.actors.values():
            actor._kill_gthreads()
        for actor in room.actors.values():
            self.container.save_actor(actor)
        self.container.save_room(room)

    def request_admin_token(self, game_id, room_id):
        token = self._create_token()
        self.admin_connections[token] = AdminConnection(game_id, room_id, token)
        return token

    def admin_connects(self, ws, token):
        admin_conn = self.admin_connections[token]
        log.debug("Admin conects: %s", token)
        room = self.rooms[admin_conn.game_id, admin_conn.room_id]
        queue = room.vision.connect_admin_queue()
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
        finally:
            room.vision.disconnect_admin_queue(queue)

    def admin_map(self, token, map_id):
        if token not in self.admin_connections:
            raise Exception("Not authorized")
        admin_conn = self.admin_connections[token]
        return self.room_factory.load_map(map_id)
