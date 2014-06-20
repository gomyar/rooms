
import gevent

from rooms.game import Game
from rooms.player import PlayerActor
from rooms.rpc import RPCException
from rooms.rpc import RPCWaitException
from rooms.rpc import WSGIRPCServer
from rooms.rpc import WSGIRPCClient
from rooms.rpc import request
from rooms.rpc import websocket

import logging
log = logging.getLogger("rooms.master")


class RegisteredNode(object):
    def __init__(self, host, port, rpc_conn):
        self.host = host
        self.port = port
        self.rpc_conn = rpc_conn
        self.rooms = []
        self.online = True
        self.load = 0.0

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

    def actor_enters_node(self, actor_id):
        return self.rpc_conn.call("actor_enters_node", actor_id=actor_id)

    def server_load(self):
        return self.load


class RegisteredRoom(object):
    def __init__(self, node_host, node_port, game_id, room_id):
        self.node_host = node_host
        self.node_port = node_port
        self.game_id = game_id
        self.room_id = room_id

        self.node = (node_host, node_port)
        self.online = True

    def __repr__(self):
        return "<RegisteredRoom %s-%s on %s:%s>" % (self.game_id, self.room_id,
            self.node_host, self.node_port)

    def tojson(self):
        return {"node": self.node, "game_id": self.game_id,
            "room_id": self.room_id, "online": self.online}


class MasterController(object):
    def __init__(self, master):
        self.master = master

    @request
    def all_players(self):
        return self.master.all_players()

    @request
    def register_node(self, host, port):
        return self.master.register_node(host, port)

    @request
    def offline_node(self, host, port):
        return self.master.offline_node(host, port)

    @request
    def deregister_node(self, host, port):
        return self.master.deregister_node(host, port)

    @request
    def all_nodes(self):
        return self.master.all_nodes()

    @request
    def all_games(self):
        return self.master.all_games()

    @request
    def managed_rooms(self):
        return self.master.managed_rooms()

    @request
    def players_in_game(self, game_id):
        return self.master.players_in_game(game_id)

    @request
    def is_player_in_game(self, username, game_id):
        return self.master.is_player_in_game(username, game_id)

    @request
    def request_room(self, game_id, room_id):
        return self.master.request_room(game_id, room_id)

    @request
    def actor_entered(self, game_id, room_id, actor_id, is_player, username):
        return self.master.actor_entered(game_id, room_id, actor_id, is_player,
            username)

    @request
    def report_load_stats(self, host, port, server_load):
        return self.master.report_load_stats(host, port, server_load)


class PlayerController(object):
    def __init__(self, master):
        self.master = master

    @request
    def create_game(self, owner_id):
        return self.master.create_game(owner_id)

    @request
    def join_game(self, username, game_id, room_id):
        return self.master.join_game(username, game_id, room_id)

    @request
    def player_connects(self, username, game_id):
        return self.master.player_connects(username, game_id)

    @websocket
    def game_status(self, ws, game_id):
        return self.master.game_status(ws, game_id)


class Master(object):
    def __init__(self, container):
        self.nodes = dict()
        self.rooms = dict()
        self.container = container

    def all_players(self):
        return sorted([
            {"username": p.username, "game_id": p.game_id,
            "room_id": p.room_id} for \
            p in self.container.all_players()])

    def register_node(self, host, port):
        ''' Node calls this to register with cluster '''
        if (host, port) in self.nodes:
            raise RPCException("Node already registered %s:%s" % (host, port))
        self.nodes[host, port] = RegisteredNode(host, port,
            self._create_rpc_conn(host, port))

    def offline_node(self, host, port):
        ''' Node calls this prior to calling deregister node, to allow time
            to save its state '''
        if (host, port) not in self.nodes:
            raise RPCException("No such node %s:%s" % (host, port))
        self.nodes[host, port].online = False

    def deregister_node(self, host, port):
        ''' Node calls this upon deregistering from cluster '''
        if (host, port) not in self.nodes:
            raise RPCException("Node not registered %s:%s" % (host, port))
        self.nodes.pop((host, port))
        self.rooms = dict([
            ((game_id, room_id), room) for ((game_id, room_id), room) in \
            self.rooms.items() if room.node != (host, port)])

    def _create_rpc_conn(self, host, port):
        return WSGIRPCClient(host, port, 'node')

    def all_nodes(self):
        return [{'host': node.host, 'port': node.port,
            'online': node.online, 'load': node.server_load()} for node in \
            self.nodes.values()]

    def report_load_stats(self, host, port, server_load):
        self.nodes[host, port].load = float(server_load)

    def create_game(self, owner_id):
        return self.container.create_game(owner_id).game_id

    def join_game(self, username, game_id, room_id):
        ''' PlayerActor joins a game - player object created.
            script player_joins() is called on node.'''
        self._check_game_exists(game_id)
        self._check_can_join(username, game_id)
        self._check_node_offline(game_id, room_id)
        self._check_nodes_available()

        node = self._get_node_for_room(game_id, room_id)
        token = node.player_joins(username, game_id, room_id)
        return {"token": token, "node": (node.host, node.port),
            "url": "http://%s:%s/assets/index.html?"
            "token=%s&game_id=%s&username=%s" % (node.host, node.port, token,
                game_id, username)}

    def _check_game_exists(self, game_id):
        if not self.container.game_exists(game_id):
            raise Exception("Game %s does not exist" % (game_id,))

    def _check_nodes_available(self):
        if not self.nodes:
            raise RPCWaitException("System offline")

    def player_connects(self, username, game_id):
        if not self.container.player_exists(username, game_id):
            raise RPCException("No such player %s, %s" % (username, game_id))
        self._check_nodes_available()

        player = self._load_player(username, game_id)
        self._check_node_offline(game_id, player.room_id)
        node = self._get_node_for_room(game_id, player.room_id)
        token = node.request_token(username, game_id)
        return {"token": token, "node": (node.host, node.port),
            "url": "http://%s:%s/assets/index.html?"
            "token=%s&game_id=%s&username=%s" % (node.host, node.port, token,
                game_id, username)}

    def _check_can_join(self, username, game_id):
        if self.container.player_exists(username, game_id):
            raise RPCException("PlayerActor already joined %s %s" % (username,
                game_id))

    def _check_node_offline(self, game_id, room_id):
        if (game_id, room_id) in self.rooms:
            room = self.rooms[game_id, room_id]
            if room.node in self.nodes and \
                not self.nodes[room.node].online:
                raise RPCWaitException("Node offline")
            if not room.online:
                raise RPCWaitException("Room in offline")

    def _load_player(self, username, game_id):
        return self.container.load_player(username, game_id)

    def _get_node_for_room(self, game_id, room_id):
        if (game_id, room_id) not in self.rooms:
            node = self._select_available_node()
            node.manage_room(game_id, room_id)
            self.rooms[game_id, room_id] = RegisteredRoom(node.host, node.port,
                game_id, room_id)

        host, port = self.rooms[game_id, room_id].node
        return self.nodes[host, port]

    def _select_available_node(self):
        return min(self.nodes.values(), key=RegisteredNode.server_load)

    def all_games(self):
        return [{"game_id": game.game_id, "owner_id": game.owner_id} for game\
            in self.container.all_games()]

    def managed_rooms(self):
        return [room.tojson() for room in self.rooms.values()]

    def players_in_game(self, game_id):
        return [{'username': player.username, 'game_id': player.game_id,
            'room_id': player.room_id} for player in \
            self.container.players_in_game(game_id)]

    def is_player_in_game(self, username, game_id):
        return self.container.player_exists(username, game_id)

    def request_room(self, game_id, room_id):
        ''' Node calls this to request management of a new room '''
        if (game_id, room_id) in self.rooms:
            return self.rooms[game_id, room_id]
        node = self._get_node_for_room(game_id, room_id)
        return (node.host, node.port)

    def game_status(self, ws, game_id):
        for i in range(25):
            gevent.sleep(1)
            ws.send("")
            gevent.sleep(1)
            ws.send("Sending %s" % i)
        return "Done"

    def actor_entered(self, game_id, room_id, actor_id, is_player, username):
        log.debug("Actor entered %s-%s %s %s %s", game_id, room_id, actor_id,
            is_player, username)
        if (game_id, room_id) in self.rooms:
            log.debug("Room %s-%s already managed", game_id, room_id)
            host, port = self.rooms[game_id, room_id].node
            log.debug("Calling actor_enters on %s:%s", host, port)
            response = self.nodes[host, port].actor_enters_node(actor_id)
            log.debug("Response: %s", response)
            return {"node": [host, port], "token": response.get('token')}
        elif is_player == "True":
            log.debug("Room %s-%s not managed, managing room", game_id, room_id)
            node = self._get_node_for_room(game_id, room_id)
            token = node.request_token(username, game_id)
            log.debug("Managed node %s:%s for %s - %s", node.host, node.port,
                username, game_id)
            return {"node": [node.host, node.port], "token": token}
