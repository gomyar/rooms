
import gevent

from rooms.script import Script
from rooms.position import Position
from rooms.vector import create_vector, Vector
from rooms.vector import time_to_position
from rooms.timer import Timer

import logging
log = logging.getLogger("rooms.actor")


class State(dict):
    def __init__(self, actor):
        super(State, self).__init__()
        self.__dict__['actor'] = actor

    def __getattr__(self, name):
        return self.get(name, None)

    def __setattr__(self, name, value):
        self[name] = value
        self.actor._send_update()


class Actor(object):
    def __init__(self, room, actor_type, script, username=None,
            actor_id=None, room_id=None, game_id=None):
        self.room = room
        self._actor_id = actor_id
        self._room_id = room_id
        self._game_id = game_id
        self.actor_type = actor_type
        self.state = State(self)
        self.path = []
        self.vector = create_vector(Position(0, 0), Position(0, 0))
        self.script = script
        self.speed = 1.0
        self.username = username
        self.is_player = False

        self._gthread = None
        self._move_gthread = None

    def __repr__(self):
        return "<Actor %s %s in %s-%s owned by %s>" % (self.actor_type,
            self.actor_id, self.room_id, self.game_id, self.username)

    @property
    def actor_id(self):
        return self._actor_id or getattr(self, "_id", None)

    @property
    def room_id(self):
        return self.room.room_id if self.room else self._room_id

    @property
    def game_id(self):
        return self.room.game_id if self.room else self._game_id

    def kick(self):
        self._run_on_gthread(self.script.call, "kickoff", self)

    def _run_on_gthread(self, method, *args, **kwargs):
        self._kill_gthread()
        self._gthread = gevent.spawn(method, *args, **kwargs)

    def move_to(self, position, path=None):
        self.path = path or self.room.find_path(self.position, position)
        self._kill_move_gthread()
        self._move_gthread = gevent.spawn(self._move_update)

    def move_wait(self, position, path=None):
        self.move_to(position, path)
        self.sleep(self._calc_end_time())

    def _kill_move_gthread(self):
        try:
            self._move_gthread.kill()
        except:
            pass
        self._move_gthread = None

    def _kill_gthread(self):
        try:
            self._gthread.kill()
        except:
            pass
        self._gthread = None


    def _calc_end_time(self):
        from_point = self.path[0]
        total = 0
        for to_point in self.path[1:]:
            total += time_to_position(from_point, to_point, self.speed)
        return total

    def sleep(self, seconds):
        Timer.sleep(seconds)

    def script_call(self, method, *args, **kwargs):
        self._script_gthread = gevent.spawn(self.script.call, method, *args,
            **kwargs)

    def _move_update(self):
        from_point = self.path[0]
        from_time = Timer.now()
        for to_point in self.path[1:]:
            end_time = from_time + \
                time_to_position(from_point, to_point, self.speed)
            self.vector = Vector(from_point, from_time, to_point, end_time)
            log.debug("Sending update for vector change: %s", self.vector)
            self._send_update()
            from_point = to_point
            from_time = end_time
            Timer.sleep_until(end_time)

    def _send_update(self):
        self.room.actor_update(self)

    @property
    def position(self):
        return self.vector.position()

    @position.setter
    def position(self, pos):
        self.vector = create_vector(pos, pos)

    def enter(self, door):
        self.room.actor_enters(self, door)
