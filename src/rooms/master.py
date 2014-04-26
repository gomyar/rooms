
import gevent

from rooms.game import Game
from rooms.player import Player
from rooms.exception import RPCException
from rooms.rpc import WSGIRPCServer
from rooms.rpc import WSGIRPCClient
from rooms.rpc import request
from rooms.rpc import websocket


class RegisteredNode(object):
    def __init__(self, host, port, rpc_conn):
        self.host = host
        self.port = port
        self.rpc_conn = rpc_conn
        self.rooms = []

    def __repr__(self):
        return "<RegisteredNode %s:%s>" % (self.host, self.port)

    def __eq__(self, rhs):
        return rhs and type(rhs) is RegisteredNode and \
            self.host == rhs.host and self.port == rhs.port

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
    def all_players(self):
        return dict(
            (p.username, {"game_id": p.game_id, "room_id": p.room_id}) for \
            p in self.players.items())

    @request
    def register_node(self, host, port):
        ''' Node calls this to register with cluster '''
        if (host, port) in self.nodes:
            raise RPCException("Node already registered %s:%s" % (host, port))
        self.nodes[host, port] = RegisteredNode(host, port,
            self._create_rpc_conn(host, port))

    def _create_rpc_conn(self, host, port):
        return WSGIRPCClient(host, port)

    @request
    def all_nodes(self):
        return [{'host': node.host, 'port': node.port} for node in \
            self.nodes.values()]

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
        node.rpc_conn.join_game(username=username, game_id=game_id)
        player = Player(username, game_id)
        self.players[username, game_id] = player
        self.player_map[username, game_id] = (node.host, node.port)
        self.game_script.player_joins(self.games[game_id], player)
        return node

    def _select_available_node(self):
        return min(self.nodes.values(), key=RegisteredNode.load)

    @request
    def all_games(self):
        ''' List all currently active games '''
        return [{"game_id": game.game_id, "owner_id": game.owner_id} for game\
            in self.games.values()]

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
        for i in range(25):
            gevent.sleep(1)
            ws.send("")
            gevent.sleep(1)
            ws.send("Sending %s" % i)
        return "Done"
