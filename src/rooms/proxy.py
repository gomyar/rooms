
from rooms.rpc import request
from rooms.rpc import websocket


class Proxy(object):
    def __init__(self, host, port, master_host, master_port):
        self.host = host
        self.port = port
        self.master_host = master_host
        self.master_port = master_port
        self.players = dict() # username, game_id -> host, port

    @request
    def player_joins(self, username, game_id, room_id):
        pass

    @websocket
    def player_connects(self, username, game_id):
        pass

    # ... mater passthrough calls (create_game, etc.)
