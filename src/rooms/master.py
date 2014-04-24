
from rooms.game import Game
from rooms.player import Player
from rooms.exception import RPCException
from rooms.rpc import WSGIRPCServer
from rooms.rpc import request
from rooms.rpc import websocket


class RegisteredNode(object):
    def __init__(self, host, port, external_host, external_port, rpc_conn):
        self.host = host
        self.port = port
        self.external_host = external_host
        self.external_port = external_port
        self.rpc_conn = rpc_conn
        self.rooms = []

    def __repr__(self):
        return "<RegisteredNode %s:%s %s:%s>" % (self.host, self.port,
            self.external_host, self.external_port)

    def __eq__(self, rhs):
        return rhs and type(rhs) is RegisteredNode and \
            self.host == rhs.host and self.port == rhs.port and \
            self.external_host == rhs.external_host and \
            self.external_port == rhs.external_port

    def player_joins(self, username, game_id):
        self.rpc_conn.player_joins(username, game_id)

    def load(self):
        return len(self.rooms)


class Master(object):
    def __init__(self, container, game_script):
        self.nodes = dict()
        self.players = dict()
        self.player_map = dict()
        self.games = dict()
        self.container = container
        self.game_script = game_script

    @request
    def register_node(self, host, port, external_host, external_port):
        self.nodes[host, port] = RegisteredNode(host, port, external_host,
            external_port, self._create_rpc_conn(host, port))

    def _create_rpc_conn(self, host, port):
        return WSGIRPCServer(host, port)

    @request
    def create_game(self, owner_id):
        game = Game(owner_id)
        self.container.save_game(game)
        self.games[game.game_id] = game
        return game.game_id

    @request
    def join_game(self, username, game_id):
        if (username, game_id) in self.players:
            raise RPCException("Player already joined %s %s" % (username,
                game_id))
        if game_id not in self.games:
            raise RPCException("No such game %s" % (game_id))
        node = self._select_available_node()
        node.rpc_conn.join_game(username, game_id)
        player = Player(username, game_id)
        self.players[username, game_id] = player
        self.player_map[username, game_id] = (node.host, node.port)
        self.game_script.player_joins(self.games[game_id], player)
        return node

    def _select_available_node(self):
        return min(self.nodes.values(), key=RegisteredNode.load)

    @request
    def players_in_game(self, game_id):
        return self.players.values()

    @request
    def is_player_in_game(self, username, game_id):
        return (username, game_id) in self.players

    @request
    def get_node(self, username, game_id):
        return self.nodes[self.player_map[username, game_id]]

    @websocket
    def game_status(self, ws, game_id):
        return ""
