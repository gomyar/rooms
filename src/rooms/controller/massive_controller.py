
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
        self.instances = dict()
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
        for uid, instance in self.instances.items():
            if instance['node'] == (host, port):
                self.instances.pop(uid)

    def _get_or_create_player(self, player_id):
        return self.container.get_or_create_player(player_id)

    def player_info(self, player_id):
        player = self._get_or_create_player(player_id)
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

    def player_connects(self, player_id):
        log.debug("Player connects: %s", player_id)
        player = self._get_or_create_player(player_id=player_id)
        if player.area_id in self.instances:
            instance = self.instances[player.area_id]
            node = self.nodes[instance['node']]
        else:
            node = self._least_busy_node()
            instance_uid = node.client.manage_area(game_id=self._game_id(),
                area_id=player.area_id)
            instance = dict(players=[],
                node=(node.host, node.port),
                area_id=player.area_id, uid=instance_uid)
            self.instances[player.area_id] = instance

        node.client.player_joins(area_id=player.area_id,
            player_id=player_id)
        return dict(instance_id=instance['uid'], host=node.external_host,
            port=node.external_port)

    def create_account(self, player_id, start_area_name, start_room_id,
            **state):
        log.debug("Creating account %s, %s, %s", player_id,
            start_area_name, state)
        player = self._get_or_create_player(player_id=player_id)
        if player.area_id:
            if player.area_id in self.instances:
                instance = self.instances[player.area_id]
                node = self.nodes[instance['node']]
            else:
                node = self._least_busy_node()
                node.client.manage_area(game_id=self._game_id(),
                    area_id=start_area_name)
        else:
            player.state.update(state)
            node = self._least_busy_node()
            node.client.manage_area(game_id=self._game_id(),
                area_id=start_area_name)
            player.area_id = start_area_name
            player.room_id = start_room_id
            self.container.save_player(player)

    def game_info(self, game_id):
        game = self.container.load_game(game_id)
        return game.start_area_map()

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

    def manage_area(self, game_id, area_id):
        return self.node.manage_area(game_id, area_id)

    def player_joins(self, area_id, player_id):
        player = self.node.container.get_or_create_player(player_id=player_id)
        return self.node.player_joins(area_id, player)
