
from rooms.controller.admin_controller import AdminController
from rooms.config import config
from rooms.game import Game
from rooms.script_wrapper import Script
from rooms.player import Player
from rooms.wsgi_rpc import WSGIRPCClient


class RegisteredNode(object):
    def __init__(self, host, port, external_host, external_port):
        self.client = WSGIRPCClient(host, port)
        self.host = host
        self.port = port
        self.external_host = external_host
        self.external_port = external_port
        self.active = True

    def __eq__(self, rhs):
        return type(rhs) is RegisteredNode and self.host == rhs.host and \
            self.port == rhs.port and self.external_host == rhs.external_host \
            and self.external_port == self.external_port

    def external(self):
        return dict(host=self.external_host, port=self.external_port)


class MasterController(object):
    def __init__(self, node, host, port, container):
        self.node = node
        self.host = host
        self.port = port
        self.nodes = dict()
        self.areas = dict()
        self.wsgi_server = None
        self.container = container
        self.admin = AdminController(self)

    def init(self):
        self.wsgi_server = WSGIRPCServer(self.host, self.port,
            exposed_methods=dict(
                register_node=self.register_node,
                deregister_node=self.deregister_node,
                shutdown_node=self.shutdown_node,

                create_game=self.create_game,
                list_games=self.list_games,

                join_game=self.join_game,
                player_info=self.player_info,
                node_info=self.node_info,

                player_moves_area=self.player_moves_area,
                send_message=self.send_message,

                admin_list_areas=self.admin.list_areas,
                admin_show_nodes=self.admin.show_nodes,
                admin_show_area=self.admin.show_area,
                admin_connects=self.admin_connects,
            )
        )

    def start(self):
        self.wsgi_server.start()

    def register_node(self, host, port, external_host, external_port):
        self.nodes[host, port] = RegisteredNode(host, port, external_host,
            external_port)

    def deregister_node(self, host, port):
        self.nodes[host, port].active = False

    def shutdown_node(self, host, port):
        self.nodes.pop((host, port))

    def create_game(self, owner_username, options):
        game = Game()
        game.owner_id = owner_username
        game_script = Script(self.node.game_script)
        game_script.create_game(game, **options)
        self.container.save_game(game)
        return game

    def list_games(self):
        games = self.container.list_games()
        return [self._game_info(g) for g in games]

    def _game_info(self, game):
        return {'game_id': game._id, 'owner': game.owner_id,
            'start_areas': game.start_areas}

    def join_game(self, username, game_id, start_area_id, start_room_id,
            **state):
        game = self.container.load_game(game_id)
        if username in game.players:
            raise Exception("User %s already joined game %s" % (username,
                game_id))
        player = Player(username)
        player.game_id = game_id
        player.area_id = start_area_id
        player.room_id = start_room_id
        player.state = state
        self.container.save_player(player)
        game.players[player.username] = player._id
        self.container.save_game(game)
        node = self._lookup_node(start_area_id)
        response = node.client.player_joins(username=username)
        return dict(host=node.external_host, port=node.external_port,
            token=response['token'])

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

    def _available_node(self):
        return self.nodes.values()[0]

    def player_info(self):
        pass

    def node_info(self):
        pass


    def player_moves_area(self):
        pass

    def send_message(self):
        pass


    def admin_list_areas(self):
        pass

    def admin_show_nodes(self):
        pass

    def admin_show_area(self):
        pass

    def admin_connects(self):
        pass


