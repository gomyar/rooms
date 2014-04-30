
import uuid

from rooms.player import Player
from rooms.rpc import WSGIRPCClient


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

    def connect_to_master(self):
        self.master_conn.register_node(host=self.master_host,
            port=self.master_port)

    def manage_room(self, game_id, room_id):
        room = self.container.load_room(game_id, room_id)
        self.rooms[game_id, room_id] = room
        room.kick()

    def player_joins(self, username, game_id, room_id):
        room = self.rooms[game_id, room_id]
        player = Player(username, game_id, room_id)
        self.players[username, game_id] = player
        player.token = self._create_token()
        self.player_script.player_joins(player, room)
        return player.token

    def _create_token(self):
        return str(uuid.uuid1())
