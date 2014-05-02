
import gevent

from rooms.game import Game
from rooms.player import Player
from rooms.rpc import RPCException
from rooms.rpc import RPCWaitException
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
        self.online = True

    def __repr__(self):
        return "<RegisteredNode %s:%s>" % (self.host, self.port)

    def __eq__(self, rhs):
        return rhs and type(rhs) is RegisteredNode and \
            self.host == rhs.host and self.port == rhs.port

    def player_joins(self, username, game_id, room_id):
        return self.rpc_conn.call("player_joins", username=username,
            game_id=game_id, room_id=room_id)

    def manage_room(self, game_id, room_id):
        self.rpc_conn.call("manage_room", game_id=game_id, room_id=room_id)

    def load(self):
        return len(self.rooms)


class Master(object):
    def __init__(self, container):
        self.nodes = dict()
        self.players = dict()
        self.player_map = dict()
        self.games = dict()
        self.rooms = dict()
        self.container = container

    @request
    def all_players(self):
        return sorted([
            ((p.username, p.game_id),
            {"game_id": p.game_id, "room_id": p.room_id, "token": p.token}) for \
            p in self.players.values()])

    @request
    def register_node(self, host, port):
        ''' Node calls this to register with cluster '''
        if (host, port) in self.nodes:
            raise RPCException("Node already registered %s:%s" % (host, port))
        self.nodes[host, port] = RegisteredNode(host, port,
            self._create_rpc_conn(host, port))

    @request
    def offline_node(self, host, port):
        ''' Node calls this prior to calling deregister node, to allow time
            to save its state '''
        if (host, port) not in self.nodes:
            raise RPCException("No such node %s:%s" % (host, port))
        self.nodes[host, port].online = False

    @request
    def deregister_node(self, host, port):
        ''' Node calls this upon deregistering from cluster '''
        if (host, port) not in self.nodes:
            raise RPCException("Node not registered %s:%s" % (host, port))
        self.nodes.pop((host, port))
        self.rooms = dict([(room, node) for (room, node) in \
            self.rooms.items() if node != (host, port)])

    def _create_rpc_conn(self, host, port):
        return WSGIRPCClient(host, port, 'node')

    @request
    def all_nodes(self):
        return [{'host': node.host, 'port': node.port,
            'online': node.online} for node in self.nodes.values()]

    @request
    def create_game(self, owner_id):
        game = self.container.create_game(owner_id)
        self.games[game.game_id] = game
        return game.game_id

    @request
    def join_game(self, username, game_id, room_id):
        ''' Player joins a game - player object created.
            script player_joins() is called on node.'''
        self._check_can_join(username, game_id)
        self._check_node_offline(game_id, room_id)

        player = self._create_player(username, game_id, room_id)

        host, port = self._get_node_for_room(game_id, room_id)
        node = self.nodes[host, port]
        self.player_map[username, game_id] = (host, port)

        token = node.player_joins(username, game_id, room_id)
        return {"token": token, "node": (node.host, node.port)}

    @request
    def player_connects(self, username, game_id):
        if (username, game_id) in self.players:
            player = self.players[username, game_id]
        else:
            player = self._load_player(username, game_id)

        node = self.nodes[host, port]
        token = node.player_connects(username, game_id)
        return {"token": token, "node": (node.host, node.port)}

    def _check_can_join(self, username, game_id):
        if (username, game_id) in self.players:
            raise RPCException("Player already joined %s %s" % (username,
                game_id))
        if game_id not in self.games:
            raise RPCException("No such game %s" % (game_id))

    def _check_node_offline(self, game_id, room_id):
        if (game_id, room_id) in self.rooms:
            host, port = self.rooms[game_id, room_id]
            if (host, port) in self.nodes and \
                not self.nodes[host, port].online:
                raise RPCWaitException("Room in transit")

    def _create_player(self, username, game_id, room_id):
        player = self.container.create_player(username, game_id, room_id)
        self.players[username, game_id] = player
        return player

    def _get_node_for_room(self, game_id, room_id):
        # game_id,
        if room_id not in self.rooms:
            node = self._select_available_node()
            node.manage_room(game_id, room_id)
            self.rooms[game_id, room_id] = (node.host, node.port)

        return self.rooms[game_id, room_id]

    def _select_available_node(self):
        return min(self.nodes.values(), key=RegisteredNode.load)

    @request
    def all_games(self):
        ''' List all currently active games '''
        return [{"game_id": game.game_id, "owner_id": game.owner_id} for game\
            in self.games.values()]

    @request
    def all_rooms(self):
        return self.rooms

    @request
    def players_in_game(self, game_id):
        return self.players.values()

    @request
    def is_player_in_game(self, username, game_id):
        return (username, game_id) in self.players

    @request
    def get_node(self, username, game_id):
        node = self.nodes[self.player_map[username, game_id]]
        return (node.host, node.port)

    @request
    def manage_room(self, node_host, node_port, game_id, room_id):
        ''' Debug only - used to force management of a room on a node '''
        if (game_id, room_id) in self.rooms:
            host, port = self.rooms[game_id, room_id]
            raise RPCException("Room %s:%s already managed on node %s:%s" % (
                game_id, room_id, host, port))
        node = self.nodes[node_host, node_port]
        self.rooms[game_id, room_id] = (node_host, node_port)
        # off to a queue with you
        node.manage_room(game_id, room_id)

    @websocket
    def game_status(self, ws, game_id):
        for i in range(25):
            gevent.sleep(1)
            ws.send("")
            gevent.sleep(1)
            ws.send("Sending %s" % i)
        return "Done"
