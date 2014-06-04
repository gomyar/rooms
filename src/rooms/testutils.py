
import gevent
from gevent.event import Event
import json

from rooms.player import PlayerActor
from rooms.room import Room
from rooms.actor import Actor
from rooms.position import Position
from rooms.timer import Timer


class MockContainer(object):
    def __init__(self, rooms=None, games=None, room_factory=None,
            actors=None, player_actors=None):
        self.rooms = rooms or {}
        self.games = games or {}
        self.actors = actors or {}
        self.player_actors = player_actors or {}
        self.room_factory = room_factory or {}
        self.gameids = 1
        self.actorids = 1
        self.playerids = 1
        self.node = MockNode()
        self.room_factory = room_factory or \
            MockRoomFactory(MockRoom("mock_game_1", "mock_room_1"))
        self.actor_updates = []

    def load_room(self, game_id, room_id):
        return self.rooms[game_id, room_id]

    def save_room(self, room):
        self.rooms[room.game_id, room.room_id] = room

    def room_exists(self, game_id, room_id):
        return (game_id, room_id) in self.rooms

    def load_player(self, username, game_id):
        return self.player_actors[username, game_id]

    def save_player(self, player):
        self.player_actors[player.username, player.game_id] = player

    def player_exists(self, username, game_id):
        return (username, game_id) in self.player_actors

    def load_game(self, game_id):
        return self.games[game_id]

    def save_game(self, game):
        self.games[game.game_id] = game

    def save_actor(self, actor):
        self.actors[actor.actor_id] = actor

    def update_actor(self, actor, **fields):
        self.actor_updates.append((actor, fields))

    def create_room(self, game_id, room_id):
        room = self.room_factory.create(game_id, room_id)
        room.geography = MockGeog()
        self.rooms[game_id, room_id] = room
        return room

    def create_actor(self, room, actor_type, script_name, player_username=None):
        actor = Actor(room, actor_type, script_name, player_username)
        actor._actor_id = "actor%s" % (self.actorids)
        self.actors[actor.actor_id] = actor
        self.actorids += 1
        return actor

    def all_games(self):
        return self.games.values()

    def all_active_games(self):
        return self.games.values()

    def create_game(self, owner_id):
        game = MockGame(owner_id, "game%s" % (self.gameids))
        self.gameids += 1
        self.save_game(game)
        return game

    def create_player(self, room, actor_type, script_name, username, game_id):
        player = PlayerActor(room, actor_type, script_name, username,
            actor_id="player%s" % (self.playerids), game_id=game_id)
        self.playerids += 1
        self.save_player(player)
        return player

    def players_in_game(self, game_id):
        return [p for p in self.player_actors.values() if p.game_id == game_id]


class MockRoom(object):
    def __init__(self, game_id, room_id):
        self._kicked_off = False
        self.room_id = room_id
        self.game_id = game_id
        self._updates = []
        self.actors = dict()
        self.topleft = Position(0, 0)
        self.bottomright = Position(10, 10)
        self.center = Position(0, 0)
        self._actor_enters = []

    def kick(self):
        self._kicked_off = True

    def find_path(self, from_pos, to_pos):
        return [from_pos, to_pos]

    def actor_update(self, actor, update):
        self._updates.append((actor, update))

    def create_actor(self, actor_type, script_name, player=None):
        actor = MockActor("mock1")
        actor.room = self
        actor.player_username = player.username if player else None
        self.actors[actor.actor_id] = actor
        return actor

    def put_actor(self, actor):
        self.actors[actor.actor_id] = actor
        actor.room = self

    def actor_enters(self, actor, door):
        self._actor_enters.append((actor, door))

    def __repr__(self):
        return "<MockRoom %s %s>" % (self.game_id, self.room_id)


class MockNode(object):
    def __init__(self):
        self._updates = []

    def actor_update(self, actor, update):
        self._updates.append((actor, update))

    def move_actor_room(self, actor, game_id, exit_room_id, exit_room_position):
        self._updates.append((actor, game_id, exit_room_id, exit_room_position))


class MockGame(object):
    def __init__(self, owner_id, game_id):
        self.owner_id = owner_id
        self.game_id = game_id


class MockScript(object):
    def __init__(self):
        self.called = []
        self.script_name = "rooms.test_scripts.basic_player"

    def call(self, method, *args, **kwargs):
        self.called.append((method, args, kwargs))

    def has_method(self, method):
        return True


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
        mock_timer._slept = 0
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
        self._slept += seconds
        event.wait(1)

    @staticmethod
    def slept():
        return Timer._instance._slept

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
    def __init__(self, actor_id=None):
        self.actor_id = actor_id
        self.script = MockScript()
        self.player_username = None

    def script_call(self, method, *args):
        self.script.call(method, *args)


class MockWebsocket(object):
    def __init__(self):
        self.updates = []

    def send(self, msg):
        self.updates.append(json.loads(msg))


class MockRoomFactory(object):
    def __init__(self, room):
        self.room = room

    def create(self, room_id, game_id):
        return self.room
