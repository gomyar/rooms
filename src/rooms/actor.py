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
        # might need to check the value has actually changed before update
        # actually, we had a diff/cache idea for that didn't we?
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
        self.kickoff_gthread = None
        self.move_gthread = None
        self.docked = dict()
        self.docked_with = None
        self.followers = set()
        self.following = None
        self.following_range = 0.0
        self.visible = True
        self.method_call = None
        self.running = True

        self._health = 1.0
        self.inventory = Inventory()
        self.circles = Circles()
        self.save_manager = Null()
        self._vision_distance = 0
        self.visible_to_all = False
        self._children = []
        self.parents = []
        self.__running_kill = False

    def __eq__(self, rhs):
        return rhs and type(rhs) == type(self) and \
            rhs.actor_id == self.actor_id

    def __repr__(self):
#        return "<Actor %s:%s>" % (self.actor_type, self.actor_id)
        return "<Actor %s:%s>" % (self.name or self.actor_id, self.actor_type)

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, health):
        if health <= 0:
            self._health = health
            self.kill()
        else:
            self._health = health
            self.send_actor_update()

    def visible_actors(self):
        return [a for a in self.room.visibility_grid.visible_actors(self) if a != self]

    @property
    def game(self):
        return self.area.game

    @property
    def area(self):
        return self.room.area

    @property
    def vision_distance(self):
        return self._vision_distance

    @vision_distance.setter
    def vision_distance(self, distance):
        self._vision_distance = distance
        self.room.visibility_grid.vision_distance_changed(self)

    @property
    def parent(self):
        if self.parents:
            return self.room.actors.get(self.parents[-1])

    def parent_id(self):
        if self.parents and self.parent:
            return self.parent.actor_id

    def load_script(self, classname):
        self.script = Script(classname)
        register_actor_script(classname, self)

    def __del__(self):
        if self.script and deregister_actor_script:
            deregister_actor_script(self.script.script_name, self)

    def kick(self):
        self.kill_gthread()
        self.running = True
        if "kickoff" in self.script:
            self._run_on_gthread(self.run_kickoff)

    def _run_on_gthread(self, method, *args, **kwargs):
        self.kickoff_gthread = gevent.spawn(method, *args, **kwargs)

    def run_kickoff(self):
        while self.running and "kickoff" in self.script:
            now = get_now()
            try:
                self.script.kickoff(self)
            except gevent.greenlet.GreenletExit, ex:
                raise
            except:
                log.exception("Exception running kickoff on %s", self)
                self.running = False
            self.sleep(min(0, max(3, get_now() - now)))

    def pause(self):
        self.running = False
        self.kill_gthread()

    def call_command(self, method_name, *args, **kwargs):
        if self.script.is_request(method_name):
            return self.script._call_function(method_name, self, *args,
                **kwargs)
        else:
            self.kill_gthread()
            self._run_on_gthread(self._background_command, method_name, *args,
                **kwargs)

    def call_request(self, method_name, player_actor, *args, **kwargs):
        if self.script.is_request(method_name):
            return self.script._call_function(method_name, self, player_actor,
                *args, **kwargs)
        else:
            raise Exception("No such request: %s" % (method_name,))

    def _background_command(self, method_name, *args, **kwargs):
        try:
            self.script._call_function(method_name, self, *args, **kwargs)
        except gevent.greenlet.GreenletExit, ex:
            raise
        except:
            log.exception("Exception calling background: %s %s, %s, %s",
                method_name, self, args, kwargs)
        self.kick()

    def kill_gthread(self):
        try:
            self.kickoff_gthread.kill()
        except:
            pass
        self.kickoff_gthread = None

    def say(self, msg):
        self.room.actor_said(self, msg)

    def actor_heard(self, actor, msg):
        pass

    def external(self):
        return dict(actor_id=self.actor_id, name=self.name,
            actor_type=self.actor_type or type(self).__name__,
            path=self.path.path, speed=self.speed, health=self.health,
            model_type=self.model_type, circle_id=self.circles.circle_id,
            visible_to_all=self.visible_to_all, parent_id=self.parent_id())

    def internal(self):
        external = self.external()
        external.update(dict(state=self.state,
            docked=bool(self.docked_with),
            docked_with=self.docked_with.actor_id if self.docked_with else None,
            docked_actors=self.docked_actor_map(),
            circles=self.circles.circles,
            inventory=dict(self.inventory.items()),
            vision_distance=self.vision_distance),
            visible=self.visible)
        return external

    def docked_actor_map(self):
        internal = dict()
        for a in self.docked.values():
            if a.actor_type not in internal:
                internal[a.actor_type] = dict()
            internal[a.actor_type][a.actor_id] = a.internal()
        return internal

    def docked_actors(self):
        actors = dict()
        for a in self.docked.values():
            if a.actor_type not in actors:
                actors[a.actor_type] = []
            actors[a.actor_type].append(a)
        return actors

    def send_actor_update(self):
        if self.docked_with:
            self.docked_with.docked_actor_update(self)
        self.room._send_actor_update(self)

    def docked_actor_update(self, actor):
        pass

    def actor_updated(self, actor):
        pass

    def _send_update(self, update_id, **kwargs):
        self.room._send_update(self, update_id, **kwargs)

    def _update(self, update_id, **kwargs):
        pass

    def actor_added(self, actor):
        self._call_script("actor_entered_vision", actor)

    def actor_removed(self, actor):
        self._call_script("actor_left_vision", actor)

    def x(self):
        return self.path.x()

    def y(self):
        return self.path.y()

    def position(self):
        return (self.x(), self.y())

    def set_position(self, position):
        self.path.set_position(position)
        self._update_actor_grid()

    def set_path(self, path):
        self.path = path
        for actor in self.docked.values():
            actor.set_path(path)
        self.send_actor_update()
        for actor in set(self.followers):
            if actor != self:
                actor._set_intercept_path(self, actor.following_range)
        if self.visible:
            self.update_grid()

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
        if self.following:
            self.following.followers.remove(self)
            self.following = None
            self.following_range = 0.0
        self.sleep(self.path.path_end_time() - get_now())

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

    def update_grid(self):
        log.debug("update_grid %s", self)
        self._kill_move_gthread()
        self.move_gthread = gevent.spawn(self._update_grid, self.path)

    def _kill_move_gthread(self):
        try:
            self.move_gthread.kill()
        except:
            pass

    def _update_grid(self, path):
        try:
            end_time = path.path_end_time()
            speed = self.path.speed()
            interval = self.room.visibility_grid.gridsize / \
                float(speed) if speed else 0
            duration = end_time - get_now()
            while interval > 0 and duration > 0:
                self.sleep(max(0, min(duration, interval)))
                duration -= interval
                self._update_actor_grid()

                speed = self.path.speed()
                interval = self.room.visibility_grid.gridsize / \
                    float(speed) if speed else 0
        except gevent.greenlet.GreenletExit, ex:
            log.debug("Normal greenlet exit")
            self._update_actor_grid()
        except Exception, e:
            log.exception("Exception updating grid")

    def _update_actor_grid(self):
        try:
            self.room.visibility_grid.update_actor_position(self)
        except Exception, e:
            log.exception("Exception updating actor %s on grid", self)

    def wait_for_path(self):
        while self.path and self.path.path_end_time() > get_now():
            self.sleep(self.path.path_end_time() - get_now())

    def _set_intercept_path(self, actor, irange):
        path = self._geog_intercept(actor.path, self.position(),
            self.speed, irange)
        if path:
            self.set_path(path)
        else:
            self.stop()
        return path

    def _geog_intercept(self, path, position, speed, irange):
        return self.room.geog.intercept(path, position, speed, irange)

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
        door = [door for door in doors if door.exit_room_id == room_id]
        door = door[0]
        self.move_to(*door.position())
        self.exit(door.actor_id)

    def stop(self):
        self.move_to(self.x(), self.y())
        self._update_actor_grid()

    def perform_action(self, action_id, seconds=0.0, **data):
        self.action = Action(action_id, seconds, data)
        self.send_actor_update()
        self.sleep(seconds)

    def sleep(self, seconds):
        self.save_manager.queue_actor(self)
        gevent.sleep(max(0, seconds))

    def exit(self, door_id):
        door = self.room.actors[door_id]
        if door.exit_area_id:
            self.room.actor_exit_to_area(self, door)
        else:
            self.room.actor_exit_to_room(self, door)

    def dock(self, actor, visible=False):
        self.docked[actor.actor_id] = actor
        actor.docked_with = self
        actor.set_path(self.path)
        actor.set_visible(visible)

    def undock(self, actor):
        self.docked.pop(actor.actor_id)
        actor.docked_with = None
        actor.set_visible(True)

    def exchange(self, actor, item_type, amount=1):
        if amount > self.inventory.get_amount(item_type):
            raise Exception("Not enough %s in inventory" % (item_type))
        self.inventory.remove_item(item_type, amount)
        actor.inventory.add_item(item_type, amount)

    def kill(self):
        if self.__running_kill:
            return
        self.__running_kill = True
        log.debug("Killing %s", self)
        self._call_kill_script()
        if self.parent:
            self.parent._children.remove(self.actor_id)
        if self.room:
            self.room.remove_actor(self)
        for actor in self.docked.values():
            actor.kill()
        if self.docked_with:
            self.docked_with.docked.pop(self.actor_id)
            self.docked_with = None
        self.running = False
        self.kill_gthread()
        self.__running_kill = False

    def _call_kill_script(self):
        self._call_script("killed")

    def _call_script(self, method, *args, **kwargs):
        if method in self.script:
            try:
                return getattr(self.script, method)(self, *args, **kwargs)
            except:
                log.exception("Exception calling script %s(%s, %s, %s)", method,
                    self, args, kwargs)

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

    def create_child(self, actor_type, actor_script, docked=True, name="",
            visible=False, visible_to_all=False, **state):
        child = self.room.create_actor(actor_type, actor_script,
            visible=(not docked) or visible, name=name,
            visible_to_all=visible_to_all,
            parents=self.parents+[self.actor_id],
            **state)
        if docked:
            self.dock(child, visible)
        self._children.append(child.actor_id)
        return child

    def is_child(self, actor):
        return actor.actor_id in self.parents

    def child_actors_in_room(self):
        return [self.room.actors[actor_id] for actor_id in self._children if \
            actor_id in self.room.actors]

    def children(self, actor_type=None):
        return [child for child in self.child_actors_in_room() if \
            not actor_type or actor_type == child.actor_type]

    def send_message(self, actor_id, room_id, area_id, message):
        self.room.send_message(self.actor_id, actor_id, room_id, area_id,
            message)

    def message_received(self, from_actor_id, message):
        if "message_received" in self.script:
            return self.script.message_received(self, from_actor_id, message)
        else:
            raise Exception("No message received script function for %s:%s" % (
                self, message))
