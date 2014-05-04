
import gevent

from rooms.script import Script


class State(dict):
    def __init__(self, actor):
        super(State, self).__init__()
        self.__dict__['actor'] = actor

    def __getattr__(self, name):
        return self.get(name, None)

    def __setattr__(self, name, value):
        self[name] = value
        # might need to check the value has actually changed before update
        # actually, we had a diff/cache idea for that didn't we?
        self.actor.send_actor_update()


class Actor(object):
    def __init__(self):
        self.script = Script()
        self.state = State(self)
        self.room = None
        self._gthread = None

    def kick(self):
        self._run_on_gthread(self.script.call, "kickoff", self)

    def _run_on_gthread(self, method, *args, **kwargs):
        self._gthread = gevent.spawn(method, *args, **kwargs)
