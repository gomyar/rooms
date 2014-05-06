
import gevent

from rooms.script import Script
from rooms.position import Position
from rooms.vector import Vector


class State(dict):
    def __init__(self, actor):
        super(State, self).__init__()
        self.__dict__['actor'] = actor

    def __getattr__(self, name):
        return self.get(name, None)

    def __setattr__(self, name, value):
        self[name] = value


class Actor(object):
    def __init__(self):
        self.script = Script()
        self.state = State(self)
        self.room = None
        self._gthread = None
        self._move_gthread = None
        self.path = []

    def kick(self):
        self._run_on_gthread(self.script.call, "kickoff", self)

    def _run_on_gthread(self, method, *args, **kwargs):
        self._gthread = gevent.spawn(method, *args, **kwargs)

    def move_to(self, position):
        self.path = self.room.find_path(self.position, position)
        self._move_gthread = gevent.spawn(self._move_update)

    def _move_update(self):
        from_point = self.path[0]
        for to_point in self.path[1:]:
            self.vector = Vector(from_point, 0, to_point, 1)
            self._send_update({'vector': self.vector})
            from_point = to_point

    def _send_update(self, update):
        pass

    @property
    def position(self):
        return Position(0, 0)
