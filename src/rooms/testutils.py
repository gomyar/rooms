
import gevent
from gevent.event import Event
import json

from rooms.player import Player
from rooms.room import Room
from rooms.position import Position
from rooms.timer import Timer


class MockContainer(object):
    def __init__(self, rooms=None, players=None, games=None):
        self.rooms = rooms or {}
        self.players = players or {}
        self.games = games or {}
        self.gameids = 1
        self.node = MockNode()

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
        room = Room(game_id, room_id, Position(0, 0), Position(50, 50),
            self.node)
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
        self._updates = []
        self.actors = dict()

    def kick(self):
        self._kicked_off = True

    def find_path(self, from_pos, to_pos):
        return [from_pos, to_pos]

    def actor_update(self, actor, update):
        self._updates.append((actor, update))


class MockNode(object):
    def __init__(self):
        self._updates = []

    def actor_update(self, actor, update):
        self._updates.append((actor, update))


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

    def find_path(self, room, from_pos, to_pos):
        return [from_pos, to_pos]


class MockTimer(Timer):
    @staticmethod
    def setup_mock():
        reload(gevent)
        mock_timer = MockTimer()
        mock_timer._old_sleep = gevent.sleep
        mock_timer._mock_now = 0
        mock_timer._sleeping_gthreads = []
        gevent.sleep = mock_timer._mock_sleep
        Timer._instance = mock_timer

    @staticmethod
    def teardown_mock():
        Timer._instance = None
        reload(gevent)

    def _sleep(self, seconds):
        self._mock_sleep(seconds)

    def _now(self):
        return self._mock_now

    def _mock_sleep(self, seconds):
        # wait for fast_forward
        event = Event()
        self._sleeping_gthreads.append((gevent.getcurrent(),
            seconds + self._mock_now, event))
        self._sleeping_gthreads.sort()
        event.wait(1)

    @staticmethod
    def fast_forward(seconds):
        Timer._instance._fast_forward(seconds)

    def _fast_forward(self, seconds):
        # ping waiting gthreads
        self._old_sleep(0)
        end_time = self._mock_now + seconds
        while self._processed(end_time):
            pass
        self._mock_now = end_time

    def _processed(self, end_time):
        for gthread, wake_time, event in list(self._sleeping_gthreads):
            if end_time >= wake_time:
                self._mock_now = wake_time
                event.set()
                self._sleeping_gthreads.remove((gthread, wake_time, event))
                self._old_sleep(0)
                return True
        return False


class MockActor(object):
    def __init__(self):
        self.script = MockScript()



class MockWebsocket(object):
    def __init__(self):
        self.updates = []

    def send(self, msg):
        self.updates.append(json.loads(msg))
