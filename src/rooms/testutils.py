
from rooms.player import Player
from rooms.room import Room
from rooms.position import Position
from rooms.waypoint import Path


class MockContainer(object):
    def __init__(self, rooms=None, players=None, games=None):
        self.rooms = rooms or {}
        self.players = players or {}
        self.games = games or {}
        self.gameids = 1

    def load_room(self, game_id, room_id):
        return self.rooms[game_id, room_id]

    def save_room(self, room):
        self.rooms[room.game_id, room.room_id] = room

    def room_exists(self, game_id, room_id):
        return (game_id, room_id) in self.rooms

    def load_player(self, username, game_id):
        return self.players[username, game_id]

    def save_player(self, player):
        self.players[player.username, player.game_id] = player

    def player_exists(self, username, game_id):
        return (username, game_id) in self.players

    def load_game(self, game_id):
        return self.games[game_id]

    def save_game(self, game):
        self.games[game.game_id] = game

    def create_room(self, game_id, room_id):
        room = Room(game_id, room_id, Position(0, 0), Position(50, 50))
        room.geography = MockGeog()
        self.rooms[game_id, room_id] = room
        return room

    def all_games(self):
        return self.games.values()

    def all_active_games(self):
        return self.games.values()

    def create_game(self, owner_id):
        game = MockGame(owner_id, "game%s" % (self.gameids))
        self.gameids += 1
        self.save_game(game)
        return game

    def create_player(self, username, game_id, room_id):
        player = Player(username, game_id, room_id)
        self.save_player(player)
        return player

    def players_in_game(self, game_id):
        return [p for p in self.players.values() if p.game_id == game_id]


class MockRoom(object):
    def __init__(self, game_id, room_id):
        self._kicked_off = False
        self.room_id = room_id
        self.game_id = game_id

    def kick(self):
        self._kicked_off = True

    def find_path(self, from_pos, to_pos):
        return Path([(from_pos, 0), (to_pos, 1)])


class MockGame(object):
    def __init__(self, owner_id, game_id):
        self.owner_id = owner_id
        self.game_id = game_id


class MockScript(object):
    def __init__(self):
        self.called = []

    def call(self, method, *args, **kwargs):
        self.called.append((method, args, kwargs))


class MockRpcClient(object):
    def __init__(self, expect=None):
        self.called = []
        self.expect = expect or {}

    def call(self, method, **kwargs):
        self.called.append((method, kwargs))
        return self.expect.get(method)


class MockGeog(object):
    def __init__(self):
        self.room = None

    def setup(self, room):
        self.room = room

    def find_path(self, from_pos, to_pos):
        return Path([(from_pos, 0), (to_pos, 1)])
