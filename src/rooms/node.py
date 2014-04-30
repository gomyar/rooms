
import uuid

from rooms.player import Player
from rooms.rpc import WSGIRPCClient
from rooms.rpc import request
from rooms.room import Room
from rooms.script import Script


class Node(object):
    def __init__(self, host, port, master_host, master_port, container):
        self.host = host
        self.port = port
        self.master_host = master_host
        self.master_port = master_port
        self.container = container
        self.rooms = dict()
        self.players = dict()
        self.master_conn = WSGIRPCClient(master_host, master_port, 'master')
        self.player_script = Script()
        self.game_script = Script()

    def connect_to_master(self):
        self.master_conn.register_node(host=self.host, port=self.port)

    def deregister(self):
        self.master_conn.deregister_node(host=self.host, port=self.port)

    @request
    def manage_room(self, game_id, room_id):
        if self.container.room_exists(game_id, room_id):
            room = self.container.load_room(game_id, room_id)
        else:
            room = Room(game_id, room_id)
            self.container.save_room(room)
            self.game_script.call("room_created", room)
        self.rooms[game_id, room_id] = room
        room.kick()

    @request
    def player_joins(self, username, game_id, room_id):
        room = self.rooms[game_id, room_id]
        player = Player(username, game_id, room_id)
        self.players[username, game_id] = player
        player.token = self._create_token()
        self.player_script.call("player_joins", player, room)
        return player.token

    def _create_token(self):
        return str(uuid.uuid1())
