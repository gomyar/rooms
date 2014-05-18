
import gevent
import uuid

from rooms.script import Script
from rooms.position import Position
from rooms.vector import create_vector, Vector
from rooms.vector import time_to_position
from rooms.timer import Timer


def _create_actor_id():
    return str(uuid.uuid1())


class State(dict):
    def __init__(self, actor):
        super(State, self).__init__()
        self.__dict__['actor'] = actor

    def __getattr__(self, name):
        return self.get(name, None)

    def __setattr__(self, name, value):
        self[name] = value


class Actor(object):
    def __init__(self, room):
        self.room = room
        self.actor_id = _create_actor_id()
        self.state = State(self)
        self.path = []
        self.vector = create_vector(Position(0, 0), Position(0, 0))
        self.script = Script()
        self.speed = 1.0

        self._gthread = None
        self._move_gthread = None

    def kick(self):
        self._run_on_gthread(self.script.call, "kickoff", self)

    def _run_on_gthread(self, method, *args, **kwargs):
        self._gthread = gevent.spawn(method, *args, **kwargs)

    def move_to(self, position, path=None):
        self.path = path or self.room.find_path(self.position, position)
        self._move_gthread = gevent.spawn(self._move_update)

    def sleep(self, seconds):
        Timer.sleep(seconds)

    def script_call(self, method, *args):
        self._script_gthread = gevent.spawn(self.script.call, method, *args)

    def _move_update(self):
        from_point = self.path[0]
        from_time = Timer.now()
        for to_point in self.path[1:]:
            end_time = from_time + \
                time_to_position(from_point, to_point, self.speed)
            self.vector = Vector(from_point, from_time, to_point, end_time)
            self._send_update({'vector': self.vector})
            from_point = to_point
            from_time = end_time
            Timer.sleep_until(end_time)

    def _send_update(self, update):
        self.room.actor_update(self, update)

    @property
    def position(self):
        return self.vector.position()
