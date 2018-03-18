
import gevent
from gevent.event import Event
from gevent import GreenletExit

from rooms.script import Script
from rooms.position import Position
from rooms.vector import create_vector, Vector
from rooms.vector import time_to_position
from rooms.timer import Timer
from rooms.utils import IDFactory
from rooms.state import SyncDict

import logging
log = logging.getLogger("rooms.actor")


def _safe_kill_gthread(gthread):
    try:
        if gthread:
            gthread.kill()
    except GreenletExit, ge:
        pass
    except:
        log.exception("Exception killing script gthread")


class AlterPath(GreenletExit):
    pass


def search_actor_test(actor, actor_type=None, state=None, visible=None,
        distance=None, distance_to=None):
    t = not actor_type or actor_type == actor.actor_type
    s = not state or \
        all(item in actor.state.items() for item in state.items())
    v = visible == None or actor.visible == visible
    d = not distance or not distance_to or \
        actor.position.distance_to(distance_to) <= distance
    return t and s and v and d


class Actor(object):
    def __init__(self, room, actor_type, script, username=None,
            actor_id=None, room_id=None, game_id=None, state=None,
            visible=True):
        self.room = room
        self.actor_id = actor_id or IDFactory.create_id()
        self.parent_id = None
        self._room_id = room_id
        self._game_id = game_id
        self.actor_type = actor_type
        self.state = SyncDict(state or {})
        self.state._set_actor(self)
        self.path = []
        self._vector = create_vector(Position(0, 0), Position(0, 0))
        self.script = script
        self._speed = 1.0
        self.username = username
        self.docked_actors = set()
        self.docked_with = None
        self._docked_with = None
        self._visible = visible

        self._script_gthread = None
        self._move_gthread = None
        self._follow_event = Event()
        self._tracking = None
        self._exception = None
        self.initialized = False

    @property
    def is_player(self):
        return False

    def __repr__(self):
        return "<Actor %s %s in %s-%s owned by %s>" % (self.actor_type,
            self.actor_id, self.room_id, self.game_id, self.username)

    @property
    def room_id(self):
        return self.room.room_id if self.room else self._room_id

    @property
    def game_id(self):
        return self.room.game_id if self.room else self._game_id

    def kick(self):
        self._kill_script_gthread()
        self._script_gthread = gevent.spawn(self._checked_script_call,
            'kickoff', self)

    def move_to(self, position, path=None):
        self.path = path or self.room.find_path(self.position, position)
        self.vector = create_vector(self.path[0], self.path[1], self._speed)
        self._kill_move_gthread()
        self._start_move_gthread()

    def _start_move_gthread(self):
        self._move_gthread = gevent.spawn(self._move_update)

    def stop(self):
        self._kill_move_gthread()
        self.position = self.position
        self.path = []

    def move_wait(self, position, path=None):
        self.move_to(position, path)
        self._move_gthread.join()

    def _move_update(self):
        from_point = self.path[0]
        from_time = Timer.now()
        while len(self.path) > 1:
            to_point = self.path[1]
            end_time = from_time + \
                time_to_position(from_point, to_point, self._speed)
            self._set_vector(create_vector(from_point, to_point, self._speed))
            from_point = to_point
            from_time = end_time
            Timer.sleep_until(end_time)
            self.path.pop(0)

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, s):
        self._speed = float(s)
        if self._move_gthread:
            self.move_to(self.path[-1])

    def _kill_move_gthread(self):
        _safe_kill_gthread(self._move_gthread)
        self._move_gthread = None

    def _kill_script_gthread(self):
        _safe_kill_gthread(self._script_gthread)
        self._script_gthread = None

    def _kill_gthreads(self):
        self._kill_move_gthread()
        self._kill_script_gthread()

    def _calc_end_time(self):
        from_point = self.path[0]
        total = 0
        for to_point in self.path[1:]:
            total += time_to_position(from_point, to_point, self._speed)
            from_point = to_point
        return total

    def sleep(self, seconds):
        Timer.sleep(seconds)

    def action(self, method, *args, **kwargs):
        self._exception = None
        if callable(method):
            self._action_call(method, args, kwargs)
        else:
            self._action_call(self.script.get_method(method), args, kwargs)

    def _action_call(self, method, args, kwargs):
        self._kill_script_gthread()
        self._script_gthread = gevent.spawn(self._checked_action_call, method,
            *args, **kwargs)

    def _checked_action_call(self, method, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except GreenletExit, ge:
            pass
        except Exception, e:
            log.exception("Exception running action: %s(%s, %s)", method,
                args, kwargs)
            self._exception = str(e)

    def script_request(self, method, *args, **kwargs):
        return self.script.call(method, *args, **kwargs)

    def script_call(self, method, *args, **kwargs):
        return self.script_request(method, self, *args, **kwargs)

    def _checked_script_call(self, method, *args, **kwargs):
        try:
            return self.script_request(method, *args, **kwargs)
        except GreenletExit, ge:
            pass
        except:
            log.exception("Exception running script: %s(%s, %s)", method,
                args, kwargs)

    def _send_state_changed(self):
        self.room.vision.actor_state_changed(self)

    @property
    def position(self):
        if self.docked_with:
            return self.docked_with.position
        else:
            return self.vector.position()

    @position.setter
    def position(self, pos):
        self._set_vector(create_vector(pos, pos))

    def distance_to(self, target):
        return self.position.distance_to(target.position)

    def _send_actor_vector_changed(self):
        if self.room:
            self.room.vision.actor_vector_changed(self)

    def _set_position(self, pos):
        if self.room:
            pos = self.room._correct_position(pos)
        self._vector = create_vector(pos, pos)

    @property
    def vector(self):
        if self.docked_with:
            return self.docked_with.vector
        else:
            return self._vector

    @vector.setter
    def vector(self, vector):
        self._set_vector(vector)
        self._kill_move_gthread()

    def _set_vector(self, vector):
        self._vector = vector
        self._send_actor_vector_changed()
        self._notify_trackers()

    def _notify_trackers(self):
        self._follow_event.set()
        self._follow_event.clear()

    def enter(self, door):
        self.room.actor_enters(self, door)

    def move_to_room(self, room_id, exit_position=None):
        self.room.move_actor_room(self, room_id, exit_position)

    def dock_with(self, actor):
        if self.docked_with:
            self.undock()
        actor.docked_actors.add(self)
        self.docked_with = actor
        self._send_state_changed()
        actor._send_state_changed()

    def remove(self):
        self.room.node.container.remove_actor(self.actor_id)
        self.room._remove_actor(self)
        for child in self.docked_actors:
            child.remove()

    def undock(self):
        if self.docked_with:
            self.position = self.docked_with.position
            self.docked_with.docked_actors.remove(self)
            self.docked_with._send_state_changed()
            self.docked_with = None
            self._send_state_changed()

    def _move_undock(self):
        if self.docked_with:
            pos = self.docked_with.position
            self._vector = create_vector(pos, pos)
            self.docked_with.docked_actors.remove(self)
            self.docked_with._send_state_changed()
            self.docked_with = None

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, isvisible):
        if isvisible == self._visible:
            return
        if isvisible:
            self._visible = isvisible
            self.room.vision.actor_becomes_visible(self)
        else:
            self._visible = isvisible
            self.room.vision.actor_becomes_invisible(self)

    def create_actor(self, actor_type, script_name, username=None,
            position=None, state=None, visible=False, docked=True):
        actor = self.room.create_actor(actor_type, script_name,
            username=self.username,
            position=self.position if docked else position, state=state,
            visible=visible, parent_id=self.actor_id)
        if docked:
            actor.dock_with(self)
        return actor

    def find_matching_path(self, target):
        diff_x = self.position.x - target.position.x
        diff_y = self.position.y - target.position.y
        diff_z = self.position.z - target.position.z
        end_pos = target.vector.end_pos.add_coords(diff_x, diff_y, diff_z)
        return [self.position, end_pos]

    def track_vector(self, target, sleep):
        try:
            self._tracking = target
            if target._tracking != self:
                target._follow_event.wait(timeout=sleep)
            else:
                self.sleep(sleep)
        finally:
            self._tracking = None

    def docked(self, actor_type=None, state=None, visible=None):
        return [a for a in self.docked_actors if \
            search_actor_test(a, actor_type, state, visible)]

    def log(self, msg, *args):
        log.debug("Actor log: %s %s - " + str(msg), self.username,
            self.actor_id, *args)

    def _get_state_val(self, pathitems, current=None):
        if not current:
            current = self.state
        if len(pathitems) > 1 and pathitems[0] in current:
            return self._get_state_val(pathitems[1:], current[pathitems[0]])
        elif pathitems and pathitems[0] in current:
            return current[pathitems[0]]
        else:
            return None

    def _set_state_val(self, pathitems, value, current=None):
        if not current:
            current = self.state
        if len(pathitems) > 1:
            if pathitems[0] not in current:
                current[pathitems[0]] = {}
            self._set_state_val(pathitems[1:], value, current[pathitems[0]])
        else:
            current[pathitems[0]] = value

    def send_event(self, data):
        self.room.vision.send_actor_event(self, data)
