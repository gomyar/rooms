
from player_actor import PlayerActor
from npc_actor import NpcActor
from door import Door

from basicsquare_geography import BasicSquareGeography

import logging
log = logging.getLogger("rooms")

from actor import FACING_NORTH
from actor import FACING_SOUTH
from actor import FACING_EAST
from actor import FACING_WEST

geog = BasicSquareGeography()


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
    def __init__(self, room_id=None, position=(0, 0), width=50, height=50,
            description=None):
        self.room_id = room_id
        self.description = description or room_id
        self.position = position
        self.width = width
        self.height = height
        self.map_objects = dict()
        self.actors = dict()
        self.area = None

    def __eq__(self, rhs):
        return rhs and self.room_id == rhs.room_id

    def __repr__(self):
        return "<Room %s at %s w:%s h:%s>" % (self.room_id,self.position,
            self.width, self.height)

    def object_at(self, x, y):
        for map_object in self.map_objects.values():
            if map_object.at(x, y):
                return True
        return False

    def get_path(self, start, end):
        start = (int(start[0]), int(start[1]))
        end = (int(end[0]), int(end[1]))
        try:
            return geog.get_path(self, start, end)
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
            map_objects=[m.external() for m in self.map_objects.values()],
        )

    def actor_enters(self, actor, door_id):
        self.actors[actor.actor_id] = actor
        actor.room = self
        actor.set_position(self.actors[door_id].position())
        self.area.actor_enters_room(self, actor, door_id)

    def player_joined_instance(self, actor):
        self.actors[actor.actor_id] = actor
        actor.room = self
        entry_x = self.position[0] + self.width / 2
        entry_y = self.position[1] + self.height / 2
        position = geog.get_available_position_closest_to(self, (entry_x, entry_y))
        actor.set_position(position)
        for player in actor.room.all_players():
            actor.instance.send_event(actor.actor_id, "actor_added",
                **actor.external(player))

    def actor_left_instance(self, actor):
        self.remove_actor(actor)

    def remove_actor(self, actor):
        self.actors.pop(actor.actor_id)
        actor.room = None
        actor.send_to_all("actor_removed",
            actor_id=actor.actor_id)

    def exit_through_door(self, actor, door_id):
        door = self.actors[door_id]
        self.actors.pop(actor.actor_id)
        actor.send_to_players_in_room("actor_exited_room",
            actor_id=actor.actor_id)
        actor.room = None
        door.exit_room.actor_enters(actor, door.exit_door_id)
        for player in actor.room.all_players():
            actor.instance.send_event(actor.actor_id, "actor_entered_room",
                **actor.external(player))
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

    def closest_player(self, position):
        players = self.all_players()
        if players:
            return min(players, key=lambda p: p.distance_to(position))
        else:
            return None

    def add_npc(self, npc, position):
        npc.set_position(position)
        npc.room = self
        npc.instance = self.area.instance
        self.actors[npc.actor_id] = npc
