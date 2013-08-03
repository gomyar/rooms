
from rooms.controller.admin_controller import AdminController
from rooms.config import config
from rooms.game import Game
from rooms.script_wrapper import Script
from rooms.player import Player


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

    def register_node(self):
        pass

    def deregister_node(self):
        pass


    def create_game(self, owner_username, options):
        game = Game()
        game.owner_id = owner_username
        game_script = Script(self.node.game_script)
        game_script.create_game(game, **options)
        self.container.save_game(game)
        return game

    def list_games(self):
        games = self.container.list_games()
        return [{'game_id': g._id, 'owner': g.owner_id} for g in games]

    def join_game(self, username, game_id, **state):
        game = self.container.load_game(game_id)
        if username in game.players:
            raise Exception("User %s already joined game %s" % (username,
                game_id))
        player = Player(username)
        player.game_id = game_id
        player.state = state
        self.container.save_player(player)
        game.players[player.username] = player._id
        self.container.save_game(game)

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


