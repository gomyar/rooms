
from rooms.timer import Timer
from rooms.script import NullScript
from rooms.script import load_script


class Master(object):
    def __init__(self, container):
        self.container = container
        self.game_script = NullScript()

    def start(self):
        pass

    def shutdown(self):
        pass

    def load_scripts(self, script_name):
        self.game_script = load_script(script_name)

    def create_game(self, owner_username, **state):
        game = self.container.create_game(owner_username, state)
        return game.game_id

    def join_game(self, game_id, username, **kwargs):
        if not self.container.game_exists(game_id):
            raise Exception("No such game: %s" % (game_id,))
        game = self.container.load_game(game_id)
        room_id = self.game_script.call("start_room", **kwargs)
        # possibly check if room actually exists here, to aid debugging
        if not room_id:
            raise Exception("No start room_id given")
        player = self.container.get_or_create_player(game_id, username,
                                                     room_id, kwargs)
        room = self._get_room(game_id, player['room_id'])
        if room['node_name']:
            return {'rooms_url': self._node_url(room['node_name'], game_id)}
        else:
            return {'rooms_url': None}

    def _node_url(self, node_name, game_id):
        node = self._get_node(node_name)
        return "http://%s/rooms/connect/%s" % (node.host, game_id)

    def list_games(self, owner_username=None):
        games = self.container.games_owned_by(owner_username)
        return [{'game_id': g.game_id, 'state': g.state,
                 'owner_username': g.owner_id,
                } for g in games]

    def list_all_games(self):
        return [{'game_id': g.game_id, 'state': g.state,
                 'owner_username': g.owner_id,
                } for g in self.container.all_games()]

    def list_players(self, username):
        players = self.container.all_players_for(username)
        return [{'game_id': p.game_id, 'status': p.status} for p in players]

    def connect_admin(self, game_id, room_id):
        admin_conn = self.container.create_admin_token(game_id, room_id, 300)
        room = self._get_room(game_id, admin_conn['room_id'])
        if room.get('node_name'):
            return {'host': self._get_node(room['node_name']).host,
                    'node_name': room['node_name'],
                    'token': admin_conn['token'],
                    'game_id': admin_conn['game_id'],
                    'room_id': admin_conn['room_id']}
        else:
            return {'wait': True}

    def _get_node(self, node_name):
        return self.container.load_node(node_name)

    def _get_room(self, game_id, room_id):
        # create/upsert room
        return self.container.request_create_room(game_id, room_id)
