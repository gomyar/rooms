import math
import inspect
import time
import uuid

import gevent
import gevent.queue

from rooms.null import Null
from rooms.waypoint import Path
from rooms.waypoint import distance
from rooms.waypoint import path_from_waypoints

from rooms.script_wrapper import Script
from rooms.script_wrapper import register_actor_script
from rooms.script_wrapper import deregister_actor_script
from rooms.inventory import Inventory
from rooms.circles import Circles
from rooms.timing import get_now

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
        self.name = ""
        self.actor_type = None
        self.path = Path()
        self.speed = 1.0
        self.room = Null()
        self.log = []
        self.script = Null()
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
        self.save_manager = Null()
        self.vision_distance = 0

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
    def game(self):
        return self.area.game

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
        if self.script.has_method("kickoff"):
            log.debug("Calling kick on %s", self)
            self._queue_script_method("kickoff", self, [], {})

    def call_command(self, method_name, *args, **kwargs):
        return self.script_call(method_name, *args, **kwargs)

    def script_call(self, method_name, *args, **kwargs):
        if self.script.is_request(method_name):
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
        finally:
            self.save_manager.queue_actor(self)

    def add_error(self, msg):
        log_entry = { 'msg': msg, 'time': time.time() }
        self.log.append(log_entry)
        if len(self.log) > 50:
            self.log.pop(0)
        self._send_update("log", **log_entry)

    def say(self, msg):
        self.room.actor_said(self, msg)

    def actor_heard(self, actor, msg):
        pass

    def external(self):
#        log.debug(" ******** %s %s", self, self.room.visibility_grid.registered_gridpoints[self])
        vision_grid = list(self.room.visibility_grid.registered_gridpoints[self] if self in self.room.visibility_grid.registered_gridpoints else [])
        vision_grid.sort()

        in_sectors = [gridpoint for gridpoint in self.room.visibility_grid.sectors if self in self.room.visibility_grid.sectors[gridpoint]]

        return dict(actor_id=self.actor_id, name=self.name,
            actor_type=self.actor_type or type(self).__name__,
            path=self.path.path, speed=self.speed, health=self.health,
            model_type=self.model_type, circle_id=self.circles.circle_id,
            vision_grid=vision_grid, in_sectors=in_sectors)

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

    def actor_updated(self, actor):
        pass

    def _send_update(self, update_id, **kwargs):
        self.room._send_update(self, update_id, **kwargs)

    def _update(self, update_id, **kwargs):
        pass

    def actor_added(self, actor):
        log.debug("Actor %s entered visibility range of %s", actor, self)

    def actor_removed(self, actor):
        log.debug("Actor %s left visibility range of %s", actor, self)

    def x(self):
        return self.path.x()

    def y(self):
        return self.path.y()

    def position(self):
        return (self.x(), self.y())

    def set_position(self, position):
        self.path.set_position(position)
        self.room.visibility_grid.update_actor_position(self)

    def set_path(self, path):
        self._set_path(path)
        self.send_actor_update()
        for actor in self.followers:
            if actor != self:
                actor._set_intercept_path(self, actor.following_range)

    def _set_path(self, path):
        self.path = path
        for actor in self.docked.values():
            actor.set_path(path)

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

    def api(self):
        return self.script.api() if self.script else dict()

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

        interval = self.room.visibility_grid.gridsize / float(self.speed)
        duration = end_time - get_now()
        while interval > 0 and duration > 0:
            self.sleep(max(0, min(duration, interval)))
            duration -= interval
            self.room.visibility_grid.update_actor_position(self)

    def intercept(self, actor, irange=0.0):
        log.debug("%s Intercepting %s at range %s", self, actor, irange)
        if self.following:
            self.following.followers.remove(self)
            self.following = None
            self.following_range = 0.0
        path = self._set_intercept_path(actor, irange)
        if path:
            actor.followers.add(self)
            self.following = actor
            self.following_range = irange
            end_time = self.path.path[1][2]
            self.sleep(end_time - get_now())

    def wait_for_path(self):
        while self.path and self.path.path_end_time() > get_now():
            self.sleep(self.path.path_end_time() - get_now())

    def _set_intercept_path(self, actor, irange):
        path = self.room.geog.intercept(actor.path, self.position(),
            self.speed, irange)
        self._set_path(path)
        self.send_actor_update()
        return path

    def animate(self, animate_id, duration=1, **kwargs):
        log.info("Animating %s(%s)", animate_id, kwargs)
        kwargs['duration'] = duration
        kwargs['start_time'] = time.time()
        kwargs['end_time'] = time.time() + duration
        kwargs['animate_id'] = animate_id
        self._send_update("animation", **kwargs)
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
        self.save_manager.queue_actor(self)
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
        if self.script and self.script.has_method("killed"):
            self._wrapped_call("killed", self)
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
        if visible == self.visible:
            return
        self.visible = visible
        if visible:
            self.room.visibility_grid.add_actor(self)
        else:
            self.room.visibility_grid.remove_actor(self)

    def find_actors(self, visible=True, ally=None, enemy=None, name=None,
            neutral=None, friendly=None, distance=None, actor_type=None):
        for target in self.room.find_actors(distance=distance,
                distance_from_point=self.position(), actor_type=actor_type,
                visible=True, name=name):
            if (ally == None or self.circles.is_allied(target)) and \
                (enemy == None or self.circles.is_enemy(target)) and \
                (neutral == None or self.circles.is_neutral(target)) and \
                (friendly == None or self.circles.is_friendly(target)) and \
                target != self:
                yield target
