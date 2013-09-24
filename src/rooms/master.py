
from rooms.game import Game
from rooms.wsgi_rpc import WSGIRPCClient
from rooms.player import Player


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

    def __repr__(self):
        return "<TegisteredNode %s:%s %s %s>" % (self.host, self.port,
            self.external_host, self.external_port)

    def external(self):
        return dict(host=self.external_host, port=self.external_port)


class Master(object):
    def __init__(self, host, port, container, game_script, game_config=None):
        self.host = host
        self.port = port
        self.container = container
        self.game_script = game_script
        self.game_config = game_config or {}

        self.nodes = dict()
        self.areas = dict()

    def start(self):
        self.wsgi_server = WSGIRPCServer(self.host, self.port,
            exposed_methods=dict(
                register_node=self.register_node,
                deregister_node=self.deregister_node,
                shutdown_node=self.shutdown_node,

                create_game=self.create_game,
                list_games=self.list_games,

                join_game=self.join_game,
                player_info=self.player_info,
                connect_to_game=self.connect_to_game,

                player_moves_area=self.player_moves_area,
                send_message=self.send_message,

                admin_list_areas=self.admin_list_areas,
                admin_show_nodes=self.admin_show_nodes,
                admin_show_area=self.admin_show_area,
                admin_connects=self.admin_connects,
            )
        )
        self.wsgi_server.start()

    def create_game(self, owner_username, **options):
        ''' User creates a game '''
        game = Game(owner_username, self.game_config)
        self.game_script.create_game(game, **options)
        self.container.save_game(game)
        return str(game._id)

    def list_games(self):
        ''' User request a list of all current Games '''
        games = self.container.list_games()
        return [self._game_info(g) for g in games]

    def _game_info(self, game):
        return {'game_id': game._id, 'owner': game.owner_id,
            'start_areas': game.start_areas}

    def join_game(self, username, game_id, **state):
        game = self.container.load_game(game_id)
        if username in game.players:
            raise Exception("User %s already joined game %s" % (username,
                game_id))
        player = Player(username, game_id)
        player.state = state
        self.game_script.player_joins(game, player)
        self.container.save_player(player)
        game.players[player.username] = player._id
        self.container.save_game(game)
        node = self._request_node(game_id, player.area_id)
        response = node.client.player_joins(username=username, game_id=game_id)
        return dict(host=node.external_host, port=node.external_port,
            token=response['token'])

    def connect_to_game(self, username, game_id):
        player = self.container.load_player(username, game_id)
        if not player:
            raise Exception("Player %s not in game %s" % (username, game_id))
        node = self._request_node(game_id, player.area_id)
        response = node.client.player_joins(username=username, game_id=game_id)
        return dict(host=node.external_host, port=node.external_port,
            token=response['token'])

    def player_info(self, username):
        ''' Request info for player Games '''
        players = self.container.list_players_for_user(username)
        return [{'game_id': player.game_id, 'area_id': player.area_id} for \
            player in players]

    def register_node(self, host, port, external_host, external_port):
        self.nodes[host, port] = RegisteredNode(host, port, external_host,
            external_port)

    def _request_node(self, game_id, area_id):
        if (game_id, area_id) in self.areas:
            area_info = self.areas[game_id, area_id]
            return self.nodes[area_info['node']]
        else:
            node = self._available_node()
            node.client.manage_area(game_id=game_id, area_id=area_id)
            area_info = dict(
                node=(node.host, node.port),
                area_id=area_id, game_id=game_id)
            self.areas[game_id, area_id] = area_info
            return node

    def _available_node(self):
        return self.nodes.values()[0]

    def player_moves_area(self, username, game_id):
        ''' Node signals a player has moved area on different node '''
        player = self.container.load_player(username=username, game_id=game_id)
        node = self._request_node(game_id, player.area_id)
        node.client.load_from_limbo(game_id=game_id, area_id=player.area_id)
        response = node.client.player_joins(username=username, game_id=game_id)
        return dict(host=node.external_host, port=node.external_port,
            token=response['token'])

    def send_message(self, from_actor_id, actor_id, game_id, area_id, room_id,
            message):
        node = self._request_node(game_id, area_id)
        node.client.send_message(from_actor_id=from_actor_id, actor_id=actor_id,
            game_id=game_id, area_id=area_id, room_id=room_id, message=message)


    def admin_list_areas(self):
        return self.areas

    def admin_show_nodes(self):
        return sorted(self.nodes.keys())

    def admin_show_area(self, game_id, area_id):
        host, port = self.areas[game_id, area_id]['node']
        rooms = self.nodes[host, port].client.admin_show_area(
            game_id=game_id, area_id=area_id)
        return rooms

    def admin_connects(self, username, game_id, area_id, room_id):
        ''' An admin user connects '''
        node = self._request_node(game_id, area_id)
        response = node.client.admin_joins(username=username, game_id=game_id,
            area_id=area_id, room_id=room_id)
        return dict(host=node.external_host, port=node.external_port,
            token=response['token'])
