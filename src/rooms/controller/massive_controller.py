
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
    def __init__(self, host, port, container):
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

                create_account=self.create_account,
                player_connects=self.player_connects,
                player_info=self.player_info,
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

    def _get_or_create_player(self, username):
        return self.container.get_or_create_player(username)

    def player_info(self, username):
        player = self._get_or_create_player(username)
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

    def player_connects(self, username):
        log.debug("Player connects: %s", username)
        player = self._get_or_create_player(username=username)
        if player.area_id in self.areas:
            area_info = self.areas[player.area_id]
            node = self.nodes[area_info['node']]
        else:
            node = self._least_busy_node()
            node.client.manage_area(area_id=player.area_id)
            area_info = dict(players=[],
                node=(node.host, node.port),
                area_id=player.area_id)
            self.area_info[player.area_id] = area_info

        node.client.player_joins(area_id=player.area_id,
            username=username)
        return dict(area_id=player.area_id, host=node.external_host,
            port=node.external_port)

    def create_account(self, username, start_area_name, start_room_id,
            **state):
        log.debug("Creating account %s, %s, %s", username,
            start_area_name, state)
        player = self._get_or_create_player(username=username)
        if player.area_id:
            if player.area_id in self.areas:
                area_info = self.areas[player.area_id]
                node = self.nodes[area_info['node']]
            else:
                node = self._least_busy_node()
                node.client.manage_area(area_id=start_area_name)
        else:
            player.state.update(state)
            node = self._least_busy_node()
            node.client.manage_area(area_id=start_area_name)
            player.area_id = start_area_name
            player.room_id = start_room_id
            self.container.save_player(player)

    def game_info(self, game_id):
        game = self.container.load_game(game_id)
        return game.start_areas

    def _least_busy_node(self):
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
        return self.node.manage_area(area_id)

    def player_joins(self, area_id, username):
        player = self.node.container.get_or_create_player(username=username)
        return self.node.player_joins(area_id, player)
