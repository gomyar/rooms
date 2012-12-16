
from collections import defaultdict

from rooms.null import Null
from player_actor import PlayerActor
from npc_actor import NpcActor
from door import Door
from rooms.config import get_config
from rooms.geography.linearopen_geography import LinearOpenGeography

from actor import FACING_NORTH
from actor import FACING_SOUTH
from actor import FACING_EAST
from actor import FACING_WEST

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
            width=self.width, height=self.height,
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
        self.put_actor(actor, position)

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
        self._send_update("put_actor", **actor.external())

    def remove_actor(self, actor):
        self.actors.pop(actor.actor_id)
        actor.room = Null()
        self._send_update("remove_actor", actor_id=actor.actor_id)

    def _send_update(self, update_id, **kwargs):
        for actor in self.actors.values():
            actor._update(update_id, **kwargs)

    def exit_through_door(self, actor, door_id):
        door = self.actors[door_id]
        self.remove_actor(actor)
        door.exit_room.put_actor(actor,
            door.exit_room.actors[door.exit_door_id].position())
        actor.add_log("You entered %s", door.exit_room.description)

    def all_doors(self):
        return filter(lambda r: type(r) is Door, self.actors.values())

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

    def all_characters(self):
        return [actor for actor in self.actors.values() if \
            issubclass(actor.__class__, CharacterActor)]

    def all_players(self):
        return [actor for actor in self.actors.values() if \
            issubclass(actor.__class__, PlayerActor)]

    def all_npcs(self):
        return [actor for actor in self.actors.values() if \
            issubclass(actor.__class__, NpcActor)]

    def has_door_to(self, room_id):
        for key, value in self.actors.items():
            if key.startswith("door_%s" % (room_id,)):
                return True
        return False

    def closest_player_to(self, actor):
        players = self.all_players()
        if players:
            return min(players, key=lambda p: p.distance_to(actor))
        else:
            return None

    def actor_said(self, actor, msg):
        for heard in self.actors.values():
            heard.actor_heard(actor, msg)
