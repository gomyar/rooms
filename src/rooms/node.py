
import uuid
import gevent
from gevent.queue import Queue
import json
import imp
import os

from rooms.player import PlayerActor
from rooms.rpc import WSGIRPCClient
from rooms.rpc import request
from rooms.rpc import websocket
from rooms.rpc import RPCException
from rooms.room import Room
from rooms.script import Script
from rooms.script import NullScript
from rooms.views import jsonview
from rooms.timer import Timer

import logging
log = logging.getLogger("rooms.node")


class GameController(object):
    def __init__(self, node):
        self.node = node

    @websocket
    def player_connects(self, ws, game_id, username, token):
        return self.node.player_connects(ws, game_id, username, token)

    @request
    def actor_call(self, game_id, username, actor_id, token, method, **kwargs):
        return self.node.actor_call(game_id, username, actor_id, token, method,
            **kwargs)


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
    def player_joins(self, username, game_id, room_id):
        return self.node.player_joins(username, game_id, room_id)

    @request
    def request_token(self, username, game_id):
        return self.node.request_token(username, game_id)

    @request
    def actor_enters_node(self, actor_id):
        return self.node.actor_enters_node(actor_id)

    @websocket
    def ping(self, ws):
        return self.node.ping(ws)


class PlayerConnection(object):
    def __init__(self, game_id, username, room, actor, token):
        self.game_id = game_id
        self.username = username
        self.room = room
        self.actor = actor
        self.token = token
        self.queues = []

    def new_queue(self):
        queue = Queue()
        self.queues.append(queue)
        return queue

    def send_message(self, message):
        log.debug("PlayerConnection: sending message to %s queues: %s",
            len(self.queues), message)
        for queue in self.queues:
            queue.put(message)


class Node(object):
    def __init__(self, host, port, master_host, master_port):
        self.host = host
        self.port = port
        self.master_host = master_host
        self.master_port = master_port
        self.rooms = dict()
        self.player_connections = dict()
        self.master_conn = WSGIRPCClient(master_host, master_port, 'master')
        self.master_player_conn = WSGIRPCClient(master_host, master_port,
            'player')

        self.scripts = dict()
        self.container = None
        self.room_factory = None

    def load_scripts(self, script_path):
        for py_file in self._list_scripts(script_path):
            script_name = os.path.splitext(py_file)[0]
            self.scripts[script_name] = Script(script_name,
                imp.load_source("rooms.scripts" + script_name,
                os.path.join(script_path, py_file)))

    def _list_scripts(self, script_path):
        return [path for path in os.listdir(script_path) if \
            path.endswith(".py") and path!= "__init__.py"]

    def connect_to_master(self):
        self.master_conn.call("register_node", host=self.host, port=self.port)

    def deregister(self):
        self.master_conn.call("offline_node", host=self.host, port=self.port)
        for (game_id, room_id), room in self.rooms.items():
            for actor in room.actors.values():
                actor._kill_gthreads()
                self.container.save_actor(actor)
            self.container.save_room(room)
        self.master_conn.call("deregister_node", host=self.host,
            port=self.port)

    def all_rooms(self):
        return [{"game_id": room.game_id, "room_id": room.room_id,
            "actors": [(key, jsonview(a)) for (key, a) in \
            room.actors.items()]} for room in self.rooms.values()]

    def all_players(self):
        return [{"username": conn.username, "game_id": conn.game_id,
            "room_id": conn.room.room_id, "token": conn.token} for conn in \
            self.player_connections.values()]

    def manage_room(self, game_id, room_id):
        if self.container.room_exists(game_id, room_id):
            room = self.container.load_room(game_id, room_id)
            for player_actor in room.player_actors():
                self._create_player_conn(player_actor)
        else:
            room = self.container.create_room(game_id, room_id)
            self.scripts['game_script'].call("room_created", room)
            for player_actor in room.player_actors():
                self._create_player_conn(player_actor)
        self.rooms[game_id, room_id] = room
        room.kick()

    def player_joins(self, username, game_id, room_id):
        room = self.rooms[game_id, room_id]
        player_actor = self.container.create_player(room, "player",
            self.scripts['player_script'], username, game_id)
        player_conn = self._create_player_conn(player_actor)
        room.put_actor(player_actor)
        self.scripts['player_script'].call("player_joins", player_actor, room)
        return player_conn.token

    def _create_player_conn(self, player_actor):
        conn_key = player_actor.username, player_actor.game_id
        if conn_key not in self.player_connections:
            player_conn = PlayerConnection(player_actor.game_id,
                player_actor.username, player_actor.room, player_actor,
                self._create_token())
            self.player_connections[conn_key] = player_conn
        return self.player_connections[conn_key]

    def request_token(self, username, game_id):
        if (username, game_id) not in self.player_connections:
            raise RPCException("No such player connected")
        return self.player_connections[username, game_id].token

    def ping(self, ws):
        for i in range(10):
            ws.send(str(i))
            gevent.sleep(1)

    def player_connects(self, ws, game_id, username, token):
        log.debug("Player conects: %s-%s %s", username, game_id, token)
        player_conn = self.player_connections[username, game_id]
        room = self.rooms[game_id, player_conn.room.room_id]
        queue = player_conn.new_queue()
        self._send_sync_to_websocket(ws, room)
        self._perform_ws_loop(player_conn, queue, ws)

    def _perform_ws_loop(self, player_conn, queue, ws):
        try:
            connected = True
            while connected:
                message = queue.get()
                log.debug("Websocket message: %s", message)
                ws.send(json.dumps(jsonview(message)))
                if message.get("command") in ['disconnect', 'redirect']:
                    connected = False
        finally:
            player_conn.queues.remove(queue)

    def _send_sync_to_websocket(self, ws, room):
        ws.send(json.dumps(self._sync_message(room)))
        for actor in room.actors.values():
            ws.send(json.dumps(
                {"command": "actor_update", "actor_id": actor.actor_id,
                "data": jsonview(actor)}))

    def _sync_message(self, room):
        return {"command": "sync", "data": {"now": Timer.now(),
            "room_id": room.room_id}}

    def actor_call(self, game_id, username, actor_id, token, method, **kwargs):
        player_conn = self.player_connections[username, game_id]
        if token != player_conn.token:
            raise Exception("Invalid token for player %s" % (username,))
        actor = player_conn.actor
        if actor.script.has_method(method):
            actor.script_call(method, actor, **kwargs)
        else:
            raise Exception("No such method %s" % (method,))

    def _connections_for(self, room):
        return [conn for conn in self.player_connections.values() if \
            conn.room == room]

    def actor_update(self, room, actor):
        log.debug("Actor update for %s in %s", actor, room)
        for player_conn in self._connections_for(room):
            log.debug("Sending to : %s : %s", player_conn.username, actor)
            player_conn.send_message({"command": "actor_update",
                "actor_id": actor.actor_id, "data": jsonview(actor)})

    def actor_removed(self, room, actor):
        log.debug("Actor removed %s from %s", actor, room)
        for player_conn in self._connections_for(room):
            log.debug("Actor removed : %s : %s", player_conn.username, actor)
            player_conn.send_message({"command": "remove_actor",
                "actor_id": actor.actor_id})

    def _request_player_connection(self, username, game_id):
        player = self._get_or_load_player(username, game_id)
        self._check_player_valid(player)
        self._setup_player_token(player)
        return player

    def _setup_player_token(self, player):
        if not player.token:
            player.token = self._create_token()

    def _check_player_valid(self, player):
        if (player.game_id, player.room_id) not in self.rooms:
            raise RPCException("Invalid player for node (no such room) %s" %
                (player,))

    def _get_or_load_player(self, username, game_id):
        if (username, game_id) not in self.player_connections:
            if not self.container.player_exists(username, game_id):
                raise RPCException("No such player %s, %s" % (username,
                    game_id))
            self.player_connections[username, game_id] = \
                self.container.load_player(username, game_id)
        return self.player_connections[username, game_id]

    def _create_token(self):
        return str(uuid.uuid1())

    def actor_enters_node(self, actor_id):
        actor = self.container.load_actor(actor_id)
        room = self.rooms[actor.game_id, actor.room_id]
        room.put_actor(actor)
        if actor.is_player:
            return {"token": self._create_player_conn(actor).token}
        else:
            return {}

    def move_actor_room(self, actor, game_id, exit_room_id, exit_position):
        gevent.spawn(self._move_actor_room, actor, game_id, exit_room_id,
            exit_position).join()

    def _move_actor_room(self, actor, game_id, exit_room_id, exit_position):
        log.debug("Moving actor %s to %s", actor, exit_room_id)
        from_room = actor.room
        if (game_id, exit_room_id) in self.rooms:
            log.debug("Moving internally")
            exit_room = self._move_actor_internal(game_id, exit_room_id, actor,
                from_room, exit_position)
            self.container.save_actor(actor)
        else:
            log.debug("Room not on this node")
            self._save_actor_to_other_room(exit_room_id, exit_position, actor,
                from_room)

            response = self._send_actor_entered_message(game_id, exit_room_id,
                actor)

            if actor.is_player:
                log.debug("It's a player")
                if (game_id, exit_room_id) in self.rooms:
                    log.debug("Room now managed by this node")
                    self._move_actor_internal(game_id, exit_room_id, actor,
                        from_room, exit_position)
                else:
                    log.debug("Redirecting to node: %s", response['node'])
                    if (actor.username, actor.game_id) in \
                        self.player_connections:
                        conn = self.player_connections[actor.username,
                            actor.game_id]
                        conn.send_message({"command": "redirect",
                            "node": response['node'],
                            "token": response['token']})
                        self.player_connections.pop((actor.username,
                            actor.game_id))

    def _send_actor_entered_message(self, game_id, exit_room_id, actor):
        response = self.master_conn.call("actor_entered", game_id=game_id,
            room_id=exit_room_id, actor_id=actor.actor_id,
            is_player=actor.is_player, username=actor.username)
        return response

    def _save_actor_to_other_room(self, exit_room_id, exit_position, actor,
            from_room):
        actor._game_id = actor.game_id
        from_room.remove_actor(actor)
        actor.position = exit_position
        actor._room_id = exit_room_id
        self.container.save_actor(actor) # (, async=False) ?

    def _move_actor_internal(self, game_id, exit_room_id, actor, from_room,
            exit_position):
        if actor.actor_id in from_room.actors:
            from_room.remove_actor(actor)
        exit_room = self.rooms[game_id, exit_room_id]
        exit_room.put_actor(actor)
        actor.position = exit_position
        if actor.is_player and \
                (actor.username, game_id) in self.player_connections:
            log.debug("Sending room sync for %s to %s-%s", exit_room, game_id,
                actor.username)
            player_conn = self.player_connections[actor.username, game_id]
            player_conn.room = exit_room
            player_conn.send_message(self._sync_message(exit_room))
            for actor in exit_room.actors.values():
                player_conn.send_message({"command": "actor_update",
                    "actor_id": actor.actor_id, "data": jsonview(actor)})
        else:
            log.debug("No connection for player %s-%s", game_id, actor.username)
