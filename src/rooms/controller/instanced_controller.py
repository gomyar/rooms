
from rooms.wsgi_rpc import WSGIRPCClient
from rooms.wsgi_rpc import WSGIRPCServer

from rooms.script_wrapper import Script
from rooms.config import get_config


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
        self.create_script = Script(get_config('scripts', 'create_script'))
        self.wsgi_server = WSGIRPCServer(self.host, self.port,
            exposed_methods=dict(
                register_node=self.register_node,
                deregister_node=self.deregister_node,

                create_game=self.create_game,
                join_game=self.join_game,
                leave_game=self.leave_game,
                player_info=self.player_info,

                list_areas=self.list_areas,
                area_info=self.area_info,
            )
        )

    def start(self):
        self.wsgi_server.start()

    def register_node(self, host, port, external_host, external_port):
        self.nodes[host, port] = RegisteredNode(host, port, external_host,
            external_port)

    def deregister_node(self, host, port):
        self.nodes.pop((host, port))
        for uid, area in self.areas.items():
            if area['node'] == (host, port):
                self.areas.pop(uid)

    def _get_or_create_player(self, player_id):
        return self.container.get_or_create_player(player_id)

    def player_info(self, player_id):
        player = self._get_or_create_player(player_id)
        return dict(
            username=player.username,
            game_id=player.game_id,
            area_id=player.area_id,
            actor_id=player.area_id,
        )

    def _create_game(self):
        return self.create_script.call_method("create_game", self)

    def create_game(self, player_id):
        # run create script
        player = self._get_or_create_player(player_id)
        game = self._create_game()
        area_id, area_name = game.start_areas[0]
        # tell node to manage area
        node = self._available_node()
        node.client.manage_area(area_id=area_id)
        area = dict(players=[],
            node=(node.host, node.port),
            area_id=area_id)
        self.areas[area_id] = area
        player.game_id = str(game._id)
        player.area_id = area_id
        self.container.save_player(player)
        return area

    def join_game(self, user_id, area_id):
        area = self.areas[area_id]
        if user_id not in area['players']:
            area['players'].append(user_id)
        node = self.nodes[area['node']]
        node.client.player_joins(area_id=area_id, player_uid=user_id)
        return dict(success=True, node=(node.external_host, node.external_port))

    def leave_game(self, user_id, area_id):
        area =  self.areas[area_id]
        area['players'].remove(user_id)
        log.debug("Player %s left area %s", user_id, area_id)
        return ""

    def list_areas(self):
        return self.areas

    def area_info(self, area_id):
        return self.areas[area_id]

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
        return self.node.manage_area(area_id)

    def player_joins(self, area_id, username):
        player = self.node.container.get_or_create_player(username=username)
        player.area_id = area_id
        return self.node.player_joins(area_id, player)
