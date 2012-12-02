import math
import inspect
import time

import gevent
import gevent.queue

from rooms.waypoint import Path
from rooms.waypoint import distance
from rooms.waypoint import get_now
from rooms.waypoint import path_from_waypoints

from rooms.script_wrapper import Script
from rooms.script_wrapper import register_actor_script
from rooms.script_wrapper import deregister_actor_script
from rooms.inventory import Inventory

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
    def __init__(self, actor_id):
        self.actor_id = actor_id
        self.actor_type = None
        self.path = Path()
        self.speed = 1.0
        self.room = None
        self.log = []
        self.script = None
        self.state = State()
        self.model_type = ""
        self.call_gthread = None
        self.call_queue = gevent.queue.Queue()
        self.docked = set()
        self.docked_with = None
        self.inventory = Inventory()

    def __eq__(self, rhs):
        return rhs and type(rhs) == type(self) and \
            rhs.actor_id == self.actor_id

    def __repr__(self):
        return "<Actor %s>" % (self.actor_id,)

    @property
    def instance(self):
        return self.room.instance

    @property
    def area(self):
        return self.room.area

    def load_script(self, classname):
        self.script = Script(classname)
        register_actor_script(classname, self)

    def __del__(self):
        if self.script and deregister_actor_script:
            deregister_actor_script(self.script.script_name, self)

    def kick(self):
        self._queue_script_method("kick", self, [], {})

    def interface_call(self, method_name, player, *args, **kwargs):
        if not self._can_call(player, method_name):
            raise Exception("Illegal interface call to %s in %s" % (method_name,
                self))
        return self.script_call(method_name, [player] + list(args), kwargs)

    def command_call(self, method_name, *args, **kwargs):
        if not self._can_call(self, method_name):
            raise Exception("Illegal command call to %s in %s" % (method_name,
                self))
        return self.script_call(method_name, args, kwargs)

    def script_call(self, method_name, args, kwargs):
        if self._is_request(method_name):
            return self._call_script_method(method_name, self, args,
                kwargs)
        else:
            self._queue_script_method(method_name, self, args, kwargs)

    def _call_script_method(self, method_name, player, args, kwargs):
        try:
            return self.script.call_method(method_name, player, *args, **kwargs)
        except Exception, e:
            log.exception("Exception calling %s(%s, %s)", method_name, args,
                kwargs)
            self.add_error("Error calling %s(%s, %s): %s" % (method_name, args,
                kwargs, e.args))
            raise

    def _queue_script_method(self, method_name, player, args, kwargs):
        if self.call_gthread:
            self.kill_gthread()
            self.remove_gthread()
        self.call_queue.put((method_name, [player] + list(args), kwargs), False)
        self.start_command_processor()

    def start_command_processor(self):
        self.call_gthread = gevent.spawn(self.process_command_queue)

    def process_command_queue(self):
        self.running = True
        while self.running:
            while not self.call_queue.empty():
                self._process_queue_item()
            self.sleep(1)
            if self.script.has_method("kickoff"):
                self._wrapped_call("kickoff", self)
            else:
                self.running = False
        self.remove_gthread()

    def kill_gthread(self):
        try:
            self.call_gthread.kill()
        except:
            pass

    def remove_gthread(self):
        self.call_gthread = None

    def _process_queue_item(self):
        method, args, kwargs = self.call_queue.get()
        self._wrapped_call(method, *args, **kwargs)

    def _wrapped_call(self, method, *args, **kwargs):
        try:
            self.script.call_method(method, *args, **kwargs)
        except gevent.greenlet.GreenletExit, ex:
            raise
        except Exception, e:
            log.exception("Exception processing %s(%s, %s)", method, args,
                kwargs)
            self.add_error("Error in %s(%s, %s): %s" % (method, args, kwargs,
                e.args))

    def add_error(self, msg):
        log_entry = { 'msg': msg, 'time': time.time() }
        self.log.append(log_entry)
        if len(self.log) > 50:
            self.log.pop(0)
        self.instance.send_to_all("log", **log_entry)

    def say(self, msg):
        self.room.actor_said(self, msg)

    def actor_heard(self, actor, msg):
        pass

    def external(self, player):
        return dict(actor_id=self.actor_id,
            actor_type=self.actor_type or type(self).__name__,
            path=self.path.path, speed=self.speed,
            model_type=self.model_type, state=self.state,
            docked=bool(self.docked_with),
            docked_with=self.docked_with.actor_id if self.docked_with else None,
            methods=self._all_exposed_methods(player))

    def send_actor_update(self):
        for actor in self.room.actors.values():
            actor.process_actor_update(self.external(actor))

    def process_actor_update(self, actor_data):
        pass

    def actor_entered_room(self, actor, door_id):
        pass

    def actor_exited_room(self, actor, door_id):
        pass

    def x(self):
        return self.path.x()

    def y(self):
        return self.path.y()

    def position(self):
        return (self.x(), self.y())

    def set_position(self, position):
        self.path.set_position(position)

    def set_path(self, path):
        self.path = path
        for actor in self.docked:
            actor.set_path(path)

    def set_waypoints(self, point_list):
        self.set_path(path_from_waypoints(point_list, self.speed))

    def distance_to(self, point):
        return distance(self.x(), self.y(), point[0], point[1])

    def _filters_equal(self, actor, filters):
        if not filters:
            return True
        for key, val in filters.items():
            if getattr(actor, key) != val:
                return False
        return True

    def _can_call(self, actor, method_name):
        return bool(self.script and self.script.can_call(actor, method_name))

    def _is_request(self, method_name):
        return bool(self.script and self.script.is_request(method_name))

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

    def remove(self):
        self.room.remove_actor(self)

    def move_to(self, x, y):
        x, y = float(x), float(y)
        path = self.room.get_path((self.x(), self.y()), (x, y))
        if not path or len(path) < 2:
            raise Exception("Wrong path: %s" % (path,))
        self.set_waypoints(path)
        self.send_actor_update()
        end_time = self.path.path_end_time()
        self.sleep(end_time - get_now())

    def intercept(self, actor):
        path = self.room.geog.intercept(actor.path, self.position(),
            self.speed)
        # times are set here
        self.set_path(path)
        self.send_actor_update()

    def move_towards(self, actor):
        self.move_to(actor.x(), actor.y())

    def move_to_room(self, room_id):
        path = self.area.find_path_to_room(self.room.room_id, room_id)
        path = path[1:]
        if not path:
            raise Exception("No path from room %s to %s" % (self.room.room_id,
                room_id))
        log.debug("Actor %s moving to room %s along path %s", self, room_id,
            path)
        for room_id in path:
            self._move_to_adjacent_room(room_id)

    def _move_to_adjacent_room(self, room_id):
        doors = self.room.all_doors()
        door = [door for door in doors if door.exit_room.room_id == room_id]
        door = door[0]
        self.move_to(*door.position())
        self.exit(door.actor_id)

    def stop(self):
        self.move_to(self.x(), self.y())

    def perform_action(self, action_id, seconds=0.0, **data):
        self.action = Action(action_id, seconds, data)
        self.send_actor_update()
        self.sleep(seconds)

    def sleep(self, seconds):
        gevent.sleep(max(0, seconds))

    def exit(self, door_id):
        self.room.exit_through_door(self, door_id)

    def dock(self, actor):
        self.docked.add(actor)
        actor.docked_with = self
        actor.set_path(self.path)
        actor.send_actor_update()

    def undock(self, actor):
        self.docked.remove(actor)
        actor.docked_with = None
        actor.send_actor_update()

    def exchange(self, actor, item_type, amount=1):
        self.inventory.remove_item(item_type, amount)
        actor.inventory.add_item(item_type, amount)

    def match_path(self, actor):
        xdiff = self.x() - actor.path.path[0][0]
        ydiff = self.y() - actor.path.path[0][1]
        newpath = [(x + xdiff, y + ydiff, t) for (x, y, t) in actor.path.path]
        log.debug("Matched path %s with %s - %s", self.path.basic_path_list(),
            actor.path.basic_path_list(), newpath)
        self.path.speed = actor.path.speed
        self.move_to(actor.path.path[-1][0], actor.path.path[-1][1])
