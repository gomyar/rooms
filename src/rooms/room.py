
from collections import defaultdict

from rooms.null import Null
from player_actor import PlayerActor
from npc_actor import NpcActor
from door import Door
from rooms.config import get_config
from rooms.geography.linearopen_geography import LinearOpenGeography
from rooms.waypoint import distance as calc_distance

from actor import FACING_NORTH
from actor import FACING_SOUTH
from actor import FACING_EAST
from actor import FACING_WEST
from actor import Actor

import logging
log = logging.getLogger("rooms")

_default_geog = LinearOpenGeography()


class RoomObject(object):
    def __init__(self, object_type, width, height, position=(0, 0),
            facing=FACING_NORTH):
        self.object_type = object_type
        self.width = width
        self.height = height
        self.position = position
        self.facing = facing

    def __repr__(self):
        return "<RoomObject %s, %s, %s, %s>" % self.wall_positions()

    def external(self):
        return dict(width=self.width, height=self.height,
            position=self.position, object_type=self.object_type,
            facing=self.facing)

    def at(self, x, y):
        return self.position[0] <= x and self.position[0] + self.width >= x \
            and self.position[1] <= y and self.position[1] + self.height >= y

    def left(self):
        return self.position[0]

    def top(self):
        return self.position[1]

    def right(self):
        return self.position[0] + self.width

    def bottom(self):
        return self.position[1] + self.height

    def wall_positions(self):
        return (self.left(), self.top(), self.right(), self.bottom())


class Room(object):
    def __init__(self, room_id=None, width=50, height=50, description=None):
        self.room_id = room_id
        self.description = description or room_id
        self.position = (0, 0)
        self.width = width
        self.height = height
        self.map_objects = dict()
        self.actors = defaultdict(Null)
        self.area = None
        self.geog = _default_geog

    def __eq__(self, rhs):
        return rhs and self.room_id == rhs.room_id

    def __repr__(self):
        return "<Room %s at %s w:%s h:%s>" % (self.room_id,self.position,
            self.width, self.height)

    @property
    def instance(self):
        return self.area.instance

    def object_at(self, x, y):
        for map_object in self.map_objects.values():
            if map_object.at(x, y):
                return True
        return False

    def get_path(self, start, end):
        start = (int(start[0]), int(start[1]))
        end = (int(end[0]), int(end[1]))
        try:
            return self.geog.get_path(self, start, end)
        except Exception, e:
            log.exception("Error %s getting path from %s to %s", e, start, end)
            raise

    def add_object(self, object_id, map_object, rel_position=(0, 0)):
        position = (self.position[0] + rel_position[0],
            self.position[1] + rel_position[1])
        map_object.position = position
        self.map_objects[object_id] = map_object

    def external(self):
        return dict(room_id=self.room_id, position=self.position,
            width=self.width, height=self.height, description=self.description,
            map_objects=dict([(obj_id, m.external()) for (obj_id, m) in \
                self.map_objects.items()]),
        )

    def actor_enters(self, actor, door_id):
        self.actors[actor.actor_id] = actor
        actor.room = self
        actor.set_position(self.geog.get_available_position_closest_to(self,
            self.actors[door_id].position()))
        self.area.actor_enters_room(self, actor, door_id)

    def actor_joined_instance(self, actor):
        self.put_actor(actor)

    def put_actor(self, actor, position=None):
        if not position:
            position = (
                self.position[0] + self.width / 2,
                self.position[1] + self.height / 2
            )
        position = self.geog.get_available_position_closest_to(self,
            position)

        self.actors[actor.actor_id] = actor
        actor.room = self
        actor.set_position(position)
        if actor.visible:
            self._send_put_actor(actor)

    def remove_actor(self, actor):
        self.actors.pop(actor.actor_id)
        actor.room = Null()
        self._send_update("remove_actor", actor_id=actor.actor_id)

    def _send_update(self, update_id, **kwargs):
        for actor in self.actors.values():
            actor._update(update_id, **kwargs)

    def _send_actor_update(self, actor):
        for target in self.actors.values():
            if target == actor:
                target._update("actor_update", **actor.internal())
            else:
                target._update("actor_update", **actor.external())

    def _send_put_actor(self, actor):
        for target in self.actors.values():
            if target == actor:
                target._update("put_actor", **actor.internal())
            else:
                target._update("put_actor", **actor.external())

    def exit_through_door(self, actor, door_id):
        door = self.actors[door_id]
        self.remove_actor(actor)
        exit_door = door.exit_room.actors[door.exit_door_id]
        door.exit_room.put_actor(actor,
            exit_door.position())
        for child in actor.docked.values():
            self.remove_actor(child)
            door.exit_room.put_actor(child,
                exit_door.position())
        actor.add_log("You entered %s", door.exit_room.description)

    def all_doors(self):
        return filter(lambda r: type(r) is Door, self.actors.values())

    def actors_by_type(self, actor_type):
        return [actor for actor in self.actors.values() if \
            actor.actor_type == actor_type]

    def left(self):
        return self.position[0]

    def top(self):
        return self.position[1]

    def right(self):
        return self.position[0] + self.width

    def bottom(self):
        return self.position[1] + self.height

    def center(self):
        return (self.position[0] + self.width / 2,
            self.position[1] + self.height / 2)

    def calculate_door_position(self, target_room):
        position = target_room.center()
        x = min(max(self.left(), position[0]), self.right())
        y = min(max(self.top(), position[1]), self.bottom())
        return x, y

    def wall_positions(self):
        return (self.left(), self.top(), self.right(), self.bottom())

    def has_door_to(self, room_id):
        for key, value in self.actors.items():
            if key.startswith("door_%s" % (room_id,)):
                return True
        return False

    def actor_said(self, actor, msg):
        for heard in self.actors.values():
            heard.actor_heard(actor, msg)

    def create_actor(self, actor_type, actor_script, position=None,
            actor_id=None, name="", **state):
        actor = Actor(actor_id)
        actor.actor_type = actor_type
        actor.model_type = actor_type
        actor.name = name
        actor.state.update(state)
        self.put_actor(actor, position)
        actor.load_script(actor_script)
        if actor.script.has_method("created"):
            actor.script.call_method("created", actor)
        actor.kick()
        return actor

    def player_actors(self):
        return [actor for actor in self.actors.values() if \
            issubclass(actor.__class__, PlayerActor)]

    def _iter_actors(self):
        for actor in self.actors.values():
            yield actor

    def find_actors(self, visible=True, distance_from_point=None,
            distance=None, actor_type=None, name=None):
        for target in self._iter_actors():
            if (visible == None or target.visible == visible) and \
                    (distance==None or calc_distance(target.x(), target.y(),
                        *distance_from_point) <  distance) and \
                    (name == None or target.name == name) and \
                    (actor_type == None or target.actor_type == actor_type):
                yield target
