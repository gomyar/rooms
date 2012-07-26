import math
import time
import inspect

from eventlet import sleep

from path_vector import Path
from path_vector import distance
from path_vector import get_now

FACING_NORTH = "north"
FACING_SOUTH = "south"
FACING_EAST = "east"
FACING_WEST = "west"


class expose:
    def __init__(self, **filters):
        self.filters = filters

    def __call__(self, func):
        func.is_exposed = True
        func.filters = self.filters
        return func


class command:
    def __init__(self, **filters):
        self.filters = filters

    def __call__(self, func):
        func.is_command = True
        func.filters = self.filters
        return func


class Action(object):
    def __init__(self, action_id, seconds=0.0, data={}):
        self.action_id = action_id
        self.seconds = seconds
        self.data = data
        self.start_time = get_now()
        self.end_time = self.start_time + seconds

    def external(self):
        return dict(action_id=self.action_id, seconds=self.seconds,
            data=self.data, start_time=self.start_time,
            end_time=self.end_time)


class Actor(object):
    def __init__(self, actor_id, position=(0, 0)):
        self.actor_id = actor_id
        self.path = Path(position)
        self.room = None
        self.instance = None
        self.state = "idle"
        self.log = []
        self.script = None
        self.action = Action("standing")
        self.stats = dict()
        self.model_type = ""

    def __eq__(self, rhs):
        return rhs and type(rhs) == type(self) and \
            rhs.actor_id == self.actor_id

    def __repr__(self):
        return "<Actor %s>" % (self.actor_id,)

    def set_state(self, state):
        self.state = state

    def interface_call(self, method_name, player, *args, **kwargs):
        if not self._can_call_method(player, method_name):
            raise Exception("Illegal interface call to %s in %s" % (method_name,
                self))
        method = self._get_method_or_script(method_name)
        return method(self, player, *args, **kwargs)

    def command_call(self, method_name, *args, **kwargs):
        if not self._can_call_command(method_name):
            raise Exception("Illegal command call to %s in %s" % (method_name,
                self))
        method = self._get_method_or_script(method_name)
        return method(self, *args, **kwargs)

    def external(self, player):
        return dict(actor_id=self.actor_id, actor_type=type(self).__name__,
            path=self.path.path_array(), speed=self.path.speed,
            action=self.action.external(), stats=self.stats,
            model_type=self.model_type,
            methods=self._all_exposed_methods(player))

    def send_actor_update(self):
        for player in self.room.all_players():
            self.send_event("actor_update",
                **self.external(player))

    def x(self):
        return self.path.x()

    def y(self):
        return self.path.y()

    def position(self):
        return (self.x(), self.y())

    def set_position(self, position):
        self.path.set_position(position)

    def set_path(self, path):
        self.path.set_path(path)

    def distance_to(self, point):
        return distance(self.x(), self.y(), point[0], point[1])

    def _filters_equal(self, actor, filters):
        for key, val in filters.items():
            if getattr(actor, key) != val:
                return False
        return True

    def _get_method_or_script(self, method_name):
        if self.script and hasattr(self.script, method_name):
            return getattr(self.script, method_name)
        else:
            return getattr(self, method_name)

    def _can_call_method(self, actor, method_name):
        func = self._get_method_or_script(method_name)
        return hasattr(func, "is_exposed") and \
            self._filters_equal(self, func.filters)

    def _can_call_command(self, method_name):
        func = self._get_method_or_script(method_name)
        return hasattr(func, "is_command") and \
            self._filters_equal(self, func.filters)

    def _all_exposed_methods(self, actor):
        if self == actor:
            return self._all_exposed_commands()
        return [m for m in dir(self) if self._can_call_method(actor, m)]

    def _all_exposed_commands(self):
        return [m for m in dir(self) if self._can_call_command(m)]

    def exposed_methods(self, actor):
        return [dict(name=method) for method in \
            self._all_exposed_methods(actor)]

    def exposed_commands(self):
        return [dict(name=command) for command in self._all_exposed_commands()]

    def add_log(self, msg, *args):
        log_entry = { 'msg': msg % args, 'time': time.time() }
        self.log.append(log_entry)
        self.send_event("log", **log_entry)

    def send_event(self, event_id, **kwargs):
        self.instance.send_event(self.actor_id, event_id, **kwargs)

    def add_chat_message(self, msg, *args):
        self.add_log(msg, *args)

    def send_to_all(self, event, **kwargs):
        self.instance.send_to_all(event, **kwargs)

    def event(self, event_id, **kwargs):
        pass

    def remove(self):
        self.room.remove_actor(self)

    def send_to_all_in_room(self, event, **kwargs):
        actor_ids = [actor.actor_id for actor in self.actors.values()]
        self.instance.send_to_players(actor_ids, event, **kwargs)


    @command()
    def move_to(self, this, x, y):
        x, y = float(x), float(y)
        path = self.room.get_path((self.x(), self.y()), (x, y))
        if not path or len(path) < 2:
            raise Exception("Wrong path: %s" % (path,))
        self.set_path(path)
        self.send_actor_update()
        end_time = self.path.path_end_time()
        sleep(end_time - get_now())

    def move_towards(self, actor):
        self.move_to(actor.x(), actor.y())

    def perform_action(self, action_id, seconds=0.0, **data):
        self.action = Action(action_id, seconds, data)
        self.send_actor_update()
        sleep(seconds)
