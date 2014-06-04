
import uuid
import gevent
import json

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


class GameController(object):
    def __init__(self, node):
        self.node = node

    @websocket
    def player_connects(self, ws, game_id, username, token):
        return self.node.player_connects(ws, game_id, username, token)

    @request
    def actor_call(self, game_id, username, actor_id, method, **kwargs):
        return self.node.actor_call(game_id, username, actor_id, method,
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

    @websocket
    def ping(self, ws):
        return self.node.ping(ws)


class Node(object):
    def __init__(self, host, port, master_host, master_port):
        self.host = host
        self.port = port
        self.master_host = master_host
        self.master_port = master_port
        self.rooms = dict()
        self.players = dict()
        self.master_conn = WSGIRPCClient(master_host, master_port, 'master')
        self.master_player_conn = WSGIRPCClient(master_host, master_port,
            'player')
        self.player_script = NullScript()
        self.game_script = NullScript()
        self.container = None
        self.room_factory = None

    def load_player_script(self, script_name):
        self.player_script = Script(script_name)

    def load_game_script(self, script_name):
        self.game_script = Script(script_name)

    def connect_to_master(self):
        self.master_conn.call("register_node", host=self.host, port=self.port)

    def deregister(self):
        self.master_conn.call("offline_node", host=self.host, port=self.port)
        for (game_id, room_id), room in self.rooms.items():
            self.container.save_room(room)
        self.master_conn.call("deregister_node", host=self.host,
            port=self.port)

    def all_rooms(self):
        return [{"game_id": room.game_id, "room_id": room.room_id,
            "actors": [(key, jsonview(a)) for (key, a) in \
            room.actors.items()]} for room in self.rooms.values()]

    def all_players(self):
        return [{"username": player.username, "game_id": player.game_id,
            "room_id": player.room_id, "token": player.token} for player in \
            self.players.values()]

    def manage_room(self, game_id, room_id):
        if self.container.room_exists(game_id, room_id):
            room = self.container.load_room(game_id, room_id)
        else:
            room = self.container.create_room(game_id, room_id)
            self.game_script.call("room_created", room)
            self.container.save_room(room)
        self.rooms[game_id, room_id] = room
        room.kick()

    def player_joins(self, username, game_id, room_id):
        room = self.rooms[game_id, room_id]
        player_actor = self.container.create_player(room, "player",
            self.player_script.script_name, username, game_id)
        self._setup_player_token(player_actor)
        self.players[username, game_id] = player_actor
        room.put_actor(player_actor)
        self.player_script.call("player_joins", player_actor, room)
        return player_actor.token

    def request_token(self, username, game_id):
        player = self._request_player_connection(username, game_id)
        return player.token

    def ping(self, ws):
        for i in range(10):
            ws.send(str(i))
            gevent.sleep(1)

    def player_connects(self, ws, game_id, username, token):
        player = self.players[username, game_id]
        ws.send(json.dumps(self._sync_message(player.room)))
        for actor in player.room.actors.values():
            ws.send(json.dumps(
                {"command": "actor_update", "actor_id": actor.actor_id,
                "data": jsonview(actor)}))
        while True:
            message = player.queue.get()
            ws.send(json.dumps(jsonview(message)))

    def _sync_message(self, room):
        return {"command": "sync", "data": {"now": Timer.now(),
            "room_id": room.room_id}}

    def actor_call(self, game_id, username, actor_id, method, **kwargs):
        player = self.players[username, game_id]
        room = self.rooms[game_id, player.room_id]
        actor = room.actors[actor_id]
        token = kwargs.pop('token')
        if token != player.token:
            raise Exception("Invalid token for player %s" % (player.username,))
        if actor.script.has_method(method):
            actor.script_call(method, actor, **kwargs)
        else:
            raise Exception("No such method %s" % (method,))

    def actor_update(self, actor, update):
        for player in self.players.values():
            player.queue.put({"command": "actor_update",
                "actor_id": actor.actor_id, "data": update})

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
        if (username, game_id) not in self.players:
            if not self.container.player_exists(username, game_id):
                raise RPCException("No such player %s, %s" % (username,
                    game_id))
            self.players[username, game_id] = self.container.load_player(
                username, game_id)
        return self.players[username, game_id]

    def _create_token(self):
        return str(uuid.uuid1())

    def _following_player(self, actor, game_id):
        return self.players.get((actor.player_username, game_id), None)

    def move_actor_room(self, actor, game_id, exit_room_id, exit_room_position):
        from_room = actor.room
        self.container.update_actor(actor, room_id=exit_room_id)
        if (game_id, exit_room_id) in self.rooms:
            exit_room = self._move_actor_internal(game_id, exit_room_id, actor,
                from_room)
            if self._following_player(actor, game_id):
                # send sync
                player = self._following_player(actor, game_id)
                player.queue.put(self._sync_message(exit_room))
        else:
            if self._following_player(actor, game_id):
                player = self._following_player(actor, game_id)
                response = self.master_player_conn.call("player_connects",
                    username=player.username, game_id=game_id)
                if response['node'] != [self.host, self.port]:
                    player.queue.put({"command": "redirect",
                        "node": response["node"], "token": response['token']})
                else:
                    exit_room = self._move_actor_internal(game_id, exit_room_id,
                        actor, from_room)
                    player.queue.put(self._sync_message(exit_room))

    def _move_actor_internal(self, game_id, exit_room_id, actor, from_room):
        from_room.actors.pop(actor.actor_id)
        exit_room = self.rooms[game_id, exit_room_id]
        exit_room.actors[actor.actor_id] = actor
        actor.room = exit_room
        return exit_room
