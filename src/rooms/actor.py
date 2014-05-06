
import gevent

from rooms.script import Script
from rooms.position import Position


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
        for point in self.path:
            self.vector = [self.position(), point]
            self.send_update()

    @property
    def position(self):
        return Position(0, 0)
