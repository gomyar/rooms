
from rooms.scriptset import ScriptSet
from rooms.rpc import request
from rooms.timer import Timer


class MasterController(object):
    def __init__(self, node):
        self.node = node

    @request
    def create_game(self, owner_username, name, description):
        return self.node.create_game(owner_username, name, description)

    @request
    def join_game(self, game_id, username, **kwargs):
        return self.node.join_game(game_id, username, **kwargs)

    @request
    def list_games(self, username):
        return self.node.list_games(username)

    @request
    def list_players(self, username):
        return self.node.list_players(username)

    @request
    def connect_player(self, game_id, username):
        return self.node.connect_player(game_id, username)


class Master(object):
    def __init__(self, container):
        self.container = container
        self.scripts = ScriptSet()

    def start(self):
        pass

    def load_scripts(self, script_path):
        self.scripts.load_scripts(script_path)

    def create_game(self, owner_username, name, description):
        game = self.container.create_game(owner_username, name, description)
        return game.game_id

    def join_game(self, game_id, username, **kwargs):
        if not self.container.game_exists(game_id):
            return {'error': 'no such game'}
        game = self.container.load_game(game_id)
        room_id = self.scripts['game_script'].call("start_room", **kwargs)
        player = self._get_player(game_id, username, room_id)
        room = self._get_room(game_id, player['room_id'])
        if room.get('node_name'):
            return {'host': self._get_node(room['node_name']).host,
                    'actor_id': player['actor_id'],
                    'token': player['token']}
        else:
            return {'wait': True}

    def list_games(self, username):
        games = self.container.games_owned_by(username)
        return [{'game_id': g.game_id, 'name': g.name,
                 'description': g.description} for g in games]

    def list_players(self, username):
        players = self.container.all_players_for(username)
        return [{'game_id': p.game_id, 'status': p.status} for p in players]

    def connect_player(self, game_id, username):
        player_conn = self.container.create_player_token(game_id, username, 300)
        if player_conn:
            room = self._get_room(game_id, player_conn['room_id'])
            if room.get('node_name'):
                return {'host': self._get_node(room['node_name']).host,
                        'actor_id': player_conn['actor_id'],
                        'token': player_conn['token']}
            else:
                return {'wait': True}
        else:
            return {'error': 'not joined'}

    def _get_node(self, node_name):
        return self.container.load_node(node_name)

    def _get_player(self, game_id, username, room_id):
        return self.container.get_or_create_player(game_id, username, room_id)

    def _get_room(self, game_id, room_id):
        # create/upsert room
        return self.container.request_create_room(game_id, room_id)
