
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
        self.rpc_conn.call("manage_room", game_id=game_id,
            room_id=room_id)
        self.rooms.append((game_id, room_id))

    def request_token(self, username, game_id):
        return self.rpc_conn.call("request_token", username=username,
            game_id=game_id)

    def server_load(self):
        return len(self.rooms)


class Master(object):
    def __init__(self, container):
        self.nodes = dict()
        self.rooms = dict()
        self.container = container

    @request
    def all_players(self):
        return sorted([
            {"username": p.username, "game_id": p.game_id,
            "room_id": p.room_id} for \
            p in self.container.all_players()])

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
        return self.container.create_game(owner_id).game_id

    @request
    def join_game(self, username, game_id, room_id):
        ''' Player joins a game - player object created.
            script player_joins() is called on node.'''
        self._check_can_join(username, game_id)
        self._check_node_offline(game_id, room_id)
        self._check_nodes_available()

        player = self._create_player(username, game_id, room_id)

        node = self._get_node_for_room(game_id, room_id)
        token = node.player_joins(username, game_id, room_id)
        return {"token": token, "node": (node.host, node.port)}

    def _check_nodes_available(self):
        if not self.nodes:
            raise RPCWaitException("System offline")

    @request
    def player_connects(self, username, game_id):
        if not self.container.player_exists(username, game_id):
            raise RPCException("No such player %s, %s" % (username, game_id))
        self._check_nodes_available()

        player = self._load_player(username, game_id)
        node = self._get_node_for_room(game_id, player.room_id)
        token = node.request_token(username, game_id)
        return {"token": token, "node": (node.host, node.port)}

    def _check_can_join(self, username, game_id):
        if self.container.player_exists(username, game_id):
            raise RPCException("Player already joined %s %s" % (username,
                game_id))

    def _check_node_offline(self, game_id, room_id):
        if (game_id, room_id) in self.rooms:
            host, port = self.rooms[game_id, room_id]
            if (host, port) in self.nodes and \
                not self.nodes[host, port].online:
                raise RPCWaitException("Room in transit")

    def _create_player(self, username, game_id, room_id):
        return self.container.create_player(username, game_id, room_id)

    def _load_player(self, username, game_id):
        return self.container.load_player(username, game_id)

    def _get_node_for_room(self, game_id, room_id):
        if (game_id, room_id) not in self.rooms:
            node = self._select_available_node()
            node.manage_room(game_id, room_id)
            self.rooms[game_id, room_id] = (node.host, node.port)

        host, port = self.rooms[game_id, room_id]
        return self.nodes[host, port]

    def _select_available_node(self):
        return min(self.nodes.values(), key=RegisteredNode.server_load)

    @request
    def all_games(self):
        return [{"game_id": game.game_id, "owner_id": game.owner_id} for game\
            in self.container.all_games()]

    @request
    def managed_rooms(self):
        return self.rooms.items()

    @request
    def players_in_game(self, game_id):
        return [{'username': player.username, 'game_id': player.game_id,
            'room_id': player.room_id} for player in \
            self.container.players_in_game(game_id)]

    @request
    def is_player_in_game(self, username, game_id):
        return self.container.player_exists(username, game_id)

    @request
    def request_room(self, game_id, room_id):
        ''' Node calls this to request management of a new room '''
        if (game_id, room_id) in self.rooms:
            return self.rooms[game_id, room_id]
        node = self._get_node_for_room(game_id, room_id)
        return (node.host, node.port)

    @websocket
    def game_status(self, ws, game_id):
        for i in range(25):
            gevent.sleep(1)
            ws.send("")
            gevent.sleep(1)
            ws.send("Sending %s" % i)
        return "Done"
