
import uuid
import gevent
from gevent.queue import Queue
import json

from rooms.player import Player
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
        self.player_queues = dict()
        self.master_conn = WSGIRPCClient(master_host, master_port, 'master')
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
            "actors": [(key, jsonview(a)) for (key, a) in room.actors.items()]} for \
            room in self.rooms.values()]

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
        player = self._request_player_connection(username, game_id)
        room = self.rooms[game_id, room_id]
        self.player_script.call("player_joins", player, room)
        return player.token

    def request_token(self, username, game_id):
        player = self._request_player_connection(username, game_id)
        return player.token

    def ping(self, ws):
        for i in range(10):
            ws.send(str(i))
            gevent.sleep(1)

    def player_connects(self, ws, game_id, username, token):
        queue = Queue()
        player = self.players[username, game_id]
        self.player_queues[game_id, username] = queue
        room = self.rooms[game_id, player.room_id]
        ws.send(json.dumps({"command": "sync", "data": {"now": Timer.now(),
            "room_id": room.room_id}}))
        for actor in room.actors.values():
            ws.send(json.dumps(
                {"command": "actor_update", "actor_id": actor.actor_id,
                "data": jsonview(actor)}))
        while True:
            print "Waiting"
            message = queue.get()
            print "Sending"
            ws.send(json.dumps(jsonview(message)))

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
        for queue in self.player_queues.values():
            print "Adding %s" % (update,)
            queue.put({"command": "actor_update", "actor_id": actor.actor_id,
                "data": update})
            print "Queue is now %s" % (queue,)

    def _request_player_connection(self, username, game_id):
        player = self._get_or_load_player(username, game_id)
        self._check_player_valid(player)
        if not player.token:
            player.token = self._create_token()
        return player

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

    def move_actor_room(self, actor, game_id, exit_room_id, exit_room_position):
        from_room = actor.room
        if (game_id, exit_room_id) in self.rooms:
            from_room.actors.pop(actor.actor_id)
            exit_room = self.rooms[game_id, exit_room_id]
            exit_room.actors[actor.actor_id] = actor
            actor.room = exit_room
            if actor.player_username:
                player = self.players[actor.player_username, game_id]
                player.room_id = exit_room.room_id
            # inject actor in to room db
            self.container.save_actor(actor)

            # send sync
        else:
            if actor.player_username:
                player = self.players[actor.player_username, game_id]
                player.room_id = exit_room_id
                response = self.master_conn.call("player_connects",
                    game_id=game_id, room_id=exit_room_id)
                if response['node'] == [self.host, self.port]:
                    queue = self.player_queues[game_id, actor.player_username]
                    queue.put({"command": "redirect", "node": response["node"],
                        "token": response['token']})
