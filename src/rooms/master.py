
from rooms.game import Game
from rooms.player import Player


class RegisteredNode(object):
    def __init__(self, host, port, external_host, external_port):
        self.host = host
        self.port = port
        self.external_host = external_host
        self.external_port = external_port

    def __repr__(self):
        return "<RegisteredNode %s:%s %s:%s>" % (self.host, self.port,
            self.external_host, self.external_port)

    def __eq__(self, rhs):
        return rhs and type(rhs) is RegisteredNode and \
            self.host == rhs.host and self.port == rhs.port and \
            self.external_host == rhs.external_host and \
            self.external_port == rhs.external_port

    def player_joins(self, username, game_id):
        self.client.player_joins(username, game_id)


class Master(object):
    def __init__(self, container):
        self.nodes = dict()
        self.players = dict()
        self.player_map = dict()
        self.games = dict()
        self.rooms = dict()
        self.container = container

    def register_node(self, host, port, external_host, external_port):
        self.nodes[host, port] = RegisteredNode(host, port, external_host,
            external_port)

    def create_game(self, owner_id):
        game = Game(owner_id)
        self.container.save_game(game)
        self.games[game.game_id] = game
        return game.game_id

    def join_game(self, username, game_id):
        node = self.nodes.values()[0]
        node.client.join_game(username, game_id)
        self.players[username, game_id] = Player(username, game_id)
        self.player_map[username, game_id] = (node.host, node.port)
        return node

    def players_in_game(self, game_id):
        return self.players.values()

    def is_player_in_game(self, username, game_id):
        return (username, game_id) in self.players

    def get_node(self, username, game_id):
        return self.nodes[self.player_map[username, game_id]]
