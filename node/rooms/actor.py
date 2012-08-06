import math
import inspect

import eventlet

from path_vector import Path
from path_vector import distance
from path_vector import get_now

from rooms.script import Script

import logging
log = logging.getLogger("rooms.node")

FACING_NORTH = "north"
FACING_SOUTH = "south"
FACING_EAST = "east"
FACING_WEST = "west"


class State(dict):
    def __getattr__(self, name):
        return self.get(name, None)

    def __setattr__(self, name, value):
        self[name] = value


class Actor(object):
    def __init__(self, actor_id, position=(0, 0)):
        self.actor_id = actor_id
        self.path = Path(position)
        self.room = None
        self.instance = None
        self.log = []
        self.script = None
        self.state = State()
        self.model_type = ""
        self.call_gthread = None
        self.call_queue = eventlet.queue.LightQueue()

    def __eq__(self, rhs):
        return rhs and type(rhs) == type(self) and \
            rhs.actor_id == self.actor_id

    def __repr__(self):
        return "<Actor %s>" % (self.actor_id,)

    def load_script(self, classname):
        self.script = Script(classname)

    def interface_call(self, method_name, player, *args, **kwargs):
        if not self._can_call(player, method_name):
            raise Exception("Illegal interface call to %s in %s" % (method_name,
                self))
        method = self._get_method_or_script(method_name)
        self.call_queue.put((method, [self, player] + list(args), kwargs))

    def command_call(self, method_name, *args, **kwargs):
        if not self._can_call(self, method_name):
            raise Exception("Illegal command call to %s in %s" % (method_name,
                self))
        method = self._get_method_or_script(method_name)
        self.call_queue.put((method, [self] + list(args), kwargs))

    def start_command_processor(self):
        self.call_gthread = eventlet.spawn(self.process_command_queue)

    def process_command_queue(self):
        self.running = True
        while self.running:
            self._process_queue_item()

    def _process_queue_item(self):
        try:
            method, args, kwargs = self.call_queue.get()
            method(*args, **kwargs)
        except:
            log.exception("Exception processing %s(%s, %s)", method, args,
                kwargs)


    def external(self, player):
        return dict(actor_id=self.actor_id, actor_type=type(self).__name__,
            path=self.path.path_array(), speed=self.path.speed,
            state=self.state,
            model_type=self.model_type,
            methods=self._all_exposed_methods(player))

    def send_actor_update(self):
        for actor in self.room.actors.values():
            actor.event("actor_update", **self.external(actor))

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
        if not filters:
            return True
        for key, val in filters.items():
            if getattr(actor, key) != val:
                return False
        return True

    def _get_method_or_script(self, method_name):
        if self.script and self.script.has_method(method_name):
            return getattr(self.script, method_name)
        else:
            return getattr(self, method_name)

    def _can_call(self, actor, method_name):
        return bool(self.script and self.script.can_call(actor, method_name))

    def _all_exposed_methods(self, actor):
        if self == actor:
            return self._all_exposed_commands()
        return self.script.methods if self.script else []

    def _all_exposed_commands(self):
        return self.script.commands if self.script else []

    def exposed_methods(self, actor):
        return [dict(name=method) for method in \
            self._all_exposed_methods(actor)]

    def exposed_commands(self):
        return [dict(name=command) for command in self._all_exposed_commands()]

    def add_log(self, msg, *args):
        pass

    def event(self, event_id, from_actor, *args, **kwargs):
        if self.script:
            self.script.call_event_method(event_id, from_actor, *args, **kwargs)

    def remove(self):
        self.room.remove_actor(self)

    def move_to(self, x, y):
        x, y = float(x), float(y)
        path = self.room.get_path((self.x(), self.y()), (x, y))
        if not path or len(path) < 2:
            raise Exception("Wrong path: %s" % (path,))
        self.set_path(path)
        self.send_actor_update()
        end_time = self.path.path_end_time()
        self.sleep(end_time - get_now())

    def move_towards(self, actor):
        self.move_to(actor.x(), actor.y())

    def perform_action(self, action_id, seconds=0.0, **data):
        self.action = Action(action_id, seconds, data)
        self.send_actor_update()
        self.sleep(seconds)

    def sleep(self, seconds):
        eventlet.sleep(seconds)
