import math
import inspect
import time
import uuid

import gevent
import gevent.queue

from rooms.null import Null
from rooms.waypoint import Path
from rooms.waypoint import distance
from rooms.waypoint import get_now
from rooms.waypoint import path_from_waypoints

from rooms.script_wrapper import Script
from rooms.script_wrapper import register_actor_script
from rooms.script_wrapper import deregister_actor_script
from rooms.inventory import Inventory
from rooms.circles import Circles

import logging
log = logging.getLogger("rooms.node")

FACING_NORTH = "north"
FACING_SOUTH = "south"
FACING_EAST = "east"
FACING_WEST = "west"


class State(dict):
    def __init__(self, actor):
        super(State, self).__init__()
        self.__dict__['actor'] = actor

    def __getattr__(self, name):
        return self.get(name, None)

    def __setattr__(self, name, value):
        self[name] = value
        self.actor.send_actor_update()


class Actor(object):
    def __init__(self, actor_id=None):
        self.actor_id = actor_id or str(uuid.uuid1())
        self.actor_type = None
        self.path = Path()
        self.speed = 1.0
        self.room = Null()
        self.log = []
        self.script = None
        self.state = State(self)
        self.model_type = ""
        self.call_gthread = None
        self.docked = dict()
        self.docked_with = None
        self.followers = set()
        self.following = None
        self.following_range = 0.0
        self.visible = True
        self.method_call = None

        self._health = 1.0
        self.inventory = Inventory()
        self.circles = Circles()

    def __eq__(self, rhs):
        return rhs and type(rhs) == type(self) and \
            rhs.actor_id == self.actor_id

    def __repr__(self):
        return "<Actor %s:%s>" % (self.actor_type, self.actor_id)

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, health):
        self._health = health
        self.send_actor_update()

    def visible_actors(self):
        return [a for a in self.room.actors.values() if a != self and a.visible]

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
        if self.script and self.script.has_method("kickoff"):
            log.debug("Calling kick on %s", self)
            self._queue_script_method("kickoff", self, [], {})

    def interface_call(self, method_name, player, *args, **kwargs):
        return self.script_call(method_name, *([player] + list(args)), **kwargs)

    def command_call(self, method_name, *args, **kwargs):
        return self.script_call(method_name, *args, **kwargs)

    def script_call(self, method_name, *args, **kwargs):
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
        log.debug("queuing %s", method_name)
        if self.call_gthread:
            self.kill_gthread()
        self.method_call = (method_name, [player] + list(args), kwargs)
        self.call_gthread = gevent.spawn(self.run_method_call)

    def run_method_call(self):
        log.debug("run_method_call")
        self.running = True
        while self.running:
            self._process_queue_item()

            self.sleep(0)
            if self.script.has_method("kickoff") and self.running:
                self._wrapped_call("kickoff", self)
            else:
                self.running = False
        self.remove_gthread()

    def _process_queue_item(self):
        log.debug("Calling %s", self.method_call)
        if self.method_call:
            method, args, kwargs = self.method_call
            self._wrapped_call(method, *args, **kwargs)
            self.method_call = None

    def kill_gthread(self):
        try:
            self.running = False
            self.call_gthread.kill()
            self.remove_gthread()
        except:
            pass

    def remove_gthread(self):
        self.call_gthread = None

    def _wrapped_call(self, method, *args, **kwargs):
        try:
            self.script.call_method(method, *args, **kwargs)
            self.running = False
        except gevent.greenlet.GreenletExit, ex:
            raise
        except Exception, e:
            log.exception("Exception processing %s script %s(%s, %s)",
                self, method, args, kwargs)
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

    def external(self):
        return dict(actor_id=self.actor_id,
            actor_type=self.actor_type or type(self).__name__,
            path=self.path.path, speed=self.speed, health=self.health,
            model_type=self.model_type, circle_id=self.circles.circle_id)

    def internal(self):
        external = self.external()
        external.update(dict(state=self.state,
            docked=bool(self.docked_with),
            docked_with=self.docked_with.actor_id if self.docked_with else None,
            docked_actors=self._docked_internal(),
            circles=self.circles.circles))
        return external

    def _docked_internal(self):
        internal = dict()
        for a in self.docked.values():
            if a.actor_type not in internal:
                internal[a.actor_type] = []
            internal[a.actor_type].append(a.internal())
        return internal

    def send_actor_update(self):
        if self.visible:
            self.room._send_actor_update(self)

    def _update(self, update_id, **kwargs):
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
        for actor in self.docked.values():
            actor.set_path(path)
        self.send_actor_update()
        for actor in self.followers:
            if actor != self:
                actor._set_intercept_path(self, actor.following_range)

    def set_waypoints(self, point_list):
        self.set_path(path_from_waypoints(point_list, self.speed))

    def distance_to(self, actor):
        return distance(self.x(), self.y(), actor.x(), actor.y())

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
        end_time = self.path.path_end_time()
        if self.following:
            self.following.followers.remove(self)
            self.following = None
            self.following_range = 0.0
        self.sleep(end_time - get_now())

    def intercept(self, actor, irange=0.0):
        log.debug("%s Intercepting %s at range %s", self, actor, irange)
        path = self._set_intercept_path(actor, irange)
        if path:
            actor.followers.add(self)
            self.following = actor
            self.following_range = irange
            end_time = self.path.path[1][2]
            log.info("Sleeping for %s", end_time - get_now())
            self.sleep(end_time - get_now())

    def _set_intercept_path(self, actor, irange):
        path = self.room.geog.intercept(actor.path, self.position(),
            self.speed, irange)
        self.path = path
        self.send_actor_update()
        return path

    def animate(self, animate_id, duration=1, **kwargs):
        log.info("Animating %s(%s)", animate_id, kwargs)
        kwargs['duration'] = duration
        kwargs['start_time'] = time.time()
        kwargs['end_time'] = time.time() + duration
        kwargs['animate_id'] = animate_id
        self.instance.send_to_all("animation", **kwargs)
        self.sleep(duration)

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
        self.docked[actor.actor_id] = actor
        actor.docked_with = self
        actor.set_path(self.path)
        actor.set_visible(False)

    def undock(self, actor):
        self.docked.pop(actor.actor_id)
        actor.docked_with = None
        actor.set_visible(True)

    def exchange(self, actor, item_type, amount=1):
        self.inventory.remove_item(item_type, amount)
        actor.inventory.add_item(item_type, amount)

    def kill(self):
        log.debug("Killing %s", self)
        self.running = False
        if self.room:
            self.room.remove_actor(self)
        for actor in self.docked.values():
            actor.kill()
        if self.docked_with:
            self.docked_with.docked.pop(self.actor_id)
            self.docked_with = None
        self.kill_gthread()

    def set_visible(self, visible):
        self.visible = visible
        if visible:
            self.room._send_put_actor(self)
        else:
            self.room._send_update("remove_actor", actor_id=self.actor_id)
        self.send_actor_update()
