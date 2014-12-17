
import gevent
from gevent.event import Event
import json

from rooms.player import PlayerActor
from rooms.room import Room
from rooms.actor import Actor
from rooms.position import Position
from rooms.timer import Timer
from rooms.container import Container
from rooms.utils import IDFactory
from rooms.gridvision import GridVision
from rooms.player_connection import PlayerConnection
from rooms.node import Node


class MockContainer(Container):
    def __init__(self, rooms=None, games=None, room_factory=None,
            actors=None, player_actors=None):
        super(MockContainer, self).__init__(MockDbase(), MockGeog(),
            MockNode(),
            room_factory or MockRoomFactory(MockRoom("mock_game_1",
                "mock_room_1")))


class MockDbase(object):
    def __init__(self):
        self.dbases = dict(rooms={}, actors={})

    def load_object(self, obj_id, collection_name):
        return self.dbases.get(collection_name, dict()).get(obj_id).copy()

    def save_object(self, obj_dict, collection_name, db_id):
        obj_dict = obj_dict.copy()
        if collection_name not in self.dbases:
            self.dbases[collection_name] = dict()
        db_id = db_id or collection_name + "_" + \
            str(len(self.dbases[collection_name]))
        obj_dict['_id'] = db_id
        self.dbases[collection_name][db_id] = obj_dict
        return db_id

    def filter(self, collection_name, **fields):
        found = self.dbases.get(collection_name, dict()).values()
        found = [o for o in found if all([i in o.items() for \
            i in fields.items()])]
        found = [o.copy() for o in found]
        return found

    def filter_one(self, collection_name, **fields):
        result = self.filter(collection_name, **fields)
        return result[0] if result else None

    def object_exists(self, collection_name, **search_fields):
        return bool(self.filter(collection_name, **search_fields))

    def object_exists_by_id(self, collection_name, object_id):
        return bool(self.dbases[collection_name].get(object_id))

    def remove(self, collection_name, **fields):
        dbase = self.dbases.get(collection_name, [])
        keep = dict()
        for k, v in dbase.items():
            if not all([i in v.items() for i in fields.items()]):
                keep[k] = v
        self.dbases[collection_name] = keep

    def update_object_fields(self, collection_name, obj, **fields):
        objdata = self.dbases.get(collection_name, dict()).get(obj._id)
        objdata.update(fields)

    def find_and_modify(self, collection_name, modify_name, modify_value,
            **search_fields):
        found = self.dbases.get(collection_name, dict()).values()
        found = [o for o in found if all([i in o.items() for \
            i in search_fields.items()])]
        found = found[0] if found else None
        if found:
            found[modify_name] = modify_value
        return found.copy() if found else None


class MockRoom(Room):
    def __init__(self, game_id, room_id):
        self._kicked_off = False
        self.room_id = room_id
        self.game_id = game_id
        self._updates = []
        self._update_invisible = []
        self._update_visible = []
        self.actors = dict()
        self.topleft = Position(0, 0)
        self.bottomright = Position(10, 10)
        self._actor_enters = []
        self.vision = GridVision(self)

    def kick(self):
        self._kicked_off = True

    def find_path(self, from_pos, to_pos):
        return [from_pos, to_pos]

    def actor_update(self, actor):
        self._updates.append(actor)

    def actor_vector_changed(self, actor, previous_vector):
        self._updates.append(actor)

    def actor_state_changed(self, actor):
        self._updates.append(actor)

    def actor_becomes_invisible(self, actor):
        self._update_invisible.append(actor)

    def actor_becomes_visible(self, actor):
        self._update_visible.append(actor)

    def create_actor(self, actor_type, script_name, player=None, position=None,
            state=None, visible=True, username=None):
        actor = MockActor("mock1")
        actor.room = self
        actor.visible = visible
        actor.username = username
        if position:
            actor._set_position(position)
        actor.username = player.username if player else None
        self.actors[actor.actor_id] = actor
        return actor

    def put_actor(self, actor):
        self.actors[actor.actor_id] = actor
        actor.room = self

    def actor_enters(self, actor, door):
        self._actor_enters.append((actor, door))

    def __repr__(self):
        return "<MockRoom %s %s>" % (self.game_id, self.room_id)


class MockNode(Node):
    def __init__(self):
        self.scripts = {}
        self.admin_connections = {}
        self.rooms = {}
        self._updates = []

    def move_actor_room(self, actor, game_id, exit_room_id, exit_room_position):
        self._updates.append((actor, game_id, exit_room_id, exit_room_position))


class MockGame(object):
    def __init__(self, owner_id, game_id):
        self.owner_id = owner_id
        self.game_id = game_id


class MockScript(object):
    def __init__(self, expect=None):
        self.called = []
        self.script_name = "mock_script"
        self.expect = expect or {}

    def call(self, method, *args, **kwargs):
        print "Script called: %s(%s, %s)" % (method, args, kwargs)
        self.called.append((method, args, kwargs))
        return self.expect.get(method)

    def has_method(self, method):
        return True


class MockRpcClient(object):
    def __init__(self, expect=None, exceptions=None):
        self.called = []
        self.expect = expect or {}
        self.exceptions = exceptions or {}

    def call(self, method, **kwargs):
        if method in self.exceptions:
            raise self.exceptions[method]
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
        # some gthreads spawn other gthreads, this seems to work for those
        for i in range(10):
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


class MockActor(Actor):
    def __init__(self, actor_id=None):
        super(MockActor, self).__init__(MockRoom("mock_game_1", "mock_room_1"),
            "mock_actor", MockScript(), actor_id=actor_id)

    def script_call(self, method, *args):
        self.script.call(method, *args)


class MockWebsocket(object):
    def __init__(self):
        self.updates = []
        self.closed = False

    def send(self, msg):
        self.updates.append(json.loads(msg))

    def close(self):
        self.closed = True


class MockRoomFactory(object):
    def __init__(self, room):
        self.room = room

    def create(self, room_id, game_id):
        return self.room


class MockIDFactory(IDFactory):
    def __init__(self):
        self.index = 0

    @staticmethod
    def setup_mock():
        IDFactory._instance = MockIDFactory()

    @staticmethod
    def teardown_mock():
        IDFactory._instance = IDFactory()

    def _create_id(self):
        self.index += 1
        return "id%s" % self.index


class MockGridVision(object):
    def __init__(self):
        self.messages = []
        self.gridsize = 10
        self.actor_queues = []

    def actor_update(self, actor):
        self.messages.append(("actor_update", actor))

    def actor_removed(self, actor):
        self.messages.append(("actor_removed", actor))

    def actor_state_changed(self, actor):
        self.messages.append(("actor_state_changed", actor))

    def actor_vector_changed(self, actor):
        self.messages.append(("actor_vector_changed", actor))

    def actor_becomes_invisible(self, actor):
        self.messages.append(("actor_becomes_invisible", actor))

    def actor_becomes_visible(self, actor):
        self.messages.append(("actor_becomes_visible", actor))

    def add_actor(self, actor):
        pass

    def remove_actor(self, actor):
        pass
