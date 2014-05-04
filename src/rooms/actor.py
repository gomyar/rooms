
import gevent

from rooms.script import Script
from rooms.position import Position
from rooms.path import Path


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
        self.path = Path()

    def kick(self):
        self._run_on_gthread(self.script.call, "kickoff", self)

    def _run_on_gthread(self, method, *args, **kwargs):
        self._gthread = gevent.spawn(method, *args, **kwargs)

    def move_to(self, position):
        self.path = self.room.find_path(self.position, position)

    @property
    def position(self):
        return Position(0, 0)
