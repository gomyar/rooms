
from rooms.wsgi_rpc import WSGIRPCClient
from rooms.wsgi_rpc import WSGIRPCServer

from rooms.script_wrapper import Script
from rooms.config import get_config

import logging
log = logging.getLogger("rooms.mcontroller")


class RegisteredNode(object):
    def __init__(self, host, port, external_host, external_port):
        self.client = WSGIRPCClient(host, port)
        self.host = host
        self.port = port
        self.external_host = external_host
        self.external_port = external_port

    def __eq__(self, rhs):
        return type(rhs) is RegisteredNode and self.host == rhs.host and \
            self.port == rhs.port and self.external_host == rhs.external_host \
            and self.external_port == self.external_port


class MasterController(object):
    def __init__(self, node, host, port, container):
        self.node = node
        self.host = host
        self.port = port
        self.nodes = dict()
        self.areas = dict()
        self.wsgi_server = None
        self.container = container

    def init(self):
        self.wsgi_server = WSGIRPCServer(self.host, self.port,
            exposed_methods=dict(
                register_node=self.register_node,
                deregister_node=self.deregister_node,
                player_joins=self.player_joins,
                player_connects=self.player_connects,
                player_info=self.player_info,
                node_info=self.node_info,
            )
        )

    def start(self):
        self.wsgi_server.start()

    def register_node(self, host, port, external_host, external_port):
        self.nodes[host, port] = RegisteredNode(host, port, external_host,
            external_port)

    def deregister_node(self, host, port):
        self.nodes.pop((host, port))
        for uid, area_info in self.areas.items():
            if area_info['node'] == (host, port):
                self.areas.pop(uid)

    def player_info(self, username):
        ''' Player info straight from player object '''
        player = self.container.get_or_create_player(username)
        return dict(
            username=player.username,
            game_id=player.game_id,
            area_id=player.area_id,
            actor_id=player.actor_id,
        )

    def _get_managed_node(self, player):
        return node

    def _game_id(self):
        return get_config("game", "game_id")

    def player_joins(self, username, area_id, room_id, **state):
        ''' Player joins to an area running on a node '''
        log.debug("Player joins: %s", username)
        player = self.container.load_player(username=username)
        # need to double check if player already connected
        player.state.update(state)
        player.area_id = area_id
        player.room_id = room_id
        self.container.save_player(player)
        node = self._lookup_node(area_id)
        node.client.player_joins(area_id=player.area_id,
            username=username)
        return dict(host=node.external_host, port=node.external_port)

    def player_connects(self, username):
        ''' A player, already in the game, connects, requesting node info '''
        player = self.container.load_player(username=username)
        # need to double check if player already connected
        node = self._lookup_node(player.area_id)
        node.client.player_joins(area_id=player.area_id,
            username=username)
        return dict(host=node.external_host, port=node.external_port)

    def node_info(self, area_id):
        node = self._lookup_node(area_id)
        return dict(host=node.external_host, port=node.external_port)

    def _lookup_node(self, area_id):
        if area_id in self.areas:
            area_info = self.areas[area_id]
            return self.nodes[area_info['node']]
        else:
            node = self._available_node()
            node.client.manage_area(area_id=area_id)
            area_info = dict(players=[],
                node=(node.host, node.port),
                area_id=area_id)
            self.areas[area_id] = area_info
            return node

    def game_info(self, game_id):
        game = self.container.load_game(game_id)
        return game.start_areas

    def _available_node(self):
        return self.nodes.values()[0]


class ClientController(object):
    def __init__(self, node, host, port, master_host, master_port):
        self.node = node
        self.host = host
        self.port = port
        self.master_host = master_host
        self.master_port = master_port
        self.wsgi_server = None

    def register_with_master(self):
        self.master.register_node(host=self.host, port=self.port,
            external_host=self.node.host, external_port=self.node.port)

    def deregister_from_master(self):
        self.master.deregister_node(host=self.host, port=self.port)

    def init(self):
        self.master = WSGIRPCClient(self.master_host, self.master_port)
        self.wsgi_server = WSGIRPCServer(self.host, int(self.port),
            dict(manage_area=self.manage_area,
                player_joins=self.player_joins))

    def start(self):
        self.wsgi_server.start()

    def manage_area(self, area_id):
        log.debug("Managing area: %s", area_id)
        self.node.manage_area(area_id)

    def player_joins(self, area_id, username):
        player = self.node.container.load_player(username=username)
        return self.node.player_joins(area_id, player)
