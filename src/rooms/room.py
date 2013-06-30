
from collections import defaultdict

from rooms.null import Null
from player_actor import PlayerActor
from npc_actor import NpcActor
from door import Door
from rooms.config import get_config
from rooms.geography.linearopen_geography import LinearOpenGeography
from rooms.waypoint import distance as calc_distance
from rooms.visibility_grid import VisibilityGrid

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
    def __init__(self, room_id=None, width=50, height=50, description=None,
            visibility_grid_gridsize=100):
        self.room_id = room_id
        self.description = description or room_id
        self.position = (0, 0)
        self.width = width
        self.height = height
        self.map_objects = dict()
        self.actors = dict()
        self.area = None
        self.geog = _default_geog
        self.save_manager = Null()
        self.visibility_grid = VisibilityGrid(self.width, self.height,
            visibility_grid_gridsize)

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
            return self.geog.get_path(self, start, end)
        except Exception, e:
            log.exception("Error %s getting path from %s to %s", e, start, end)
            raise

    def add_object(self, object_id, map_object, rel_position=(0, 0)):
        position = (self.position[0] + rel_position[0],
            self.position[1] + rel_position[1])
        map_object.position = position
        self.map_objects[object_id] = map_object

    def external(self, map_objects=True):
        return dict(room_id=self.room_id, position=self.position,
            width=self.width, height=self.height, description=self.description,
            map_objects=dict([(obj_id, m.external()) for (obj_id, m) in \
                self.map_objects.items()]) if map_objects else None,
            visibility_grid=self.visibility_grid.external(),
        )

    def actor_enters(self, actor, door_id):
        self.actors[actor.actor_id] = actor
        actor.room = self
        actor.set_position(self.geog.get_available_position_closest_to(self,
            self.actors[door_id].position()))
        self.area.actor_enters_room(self, actor, door_id)

    def put_actor(self, actor, position=None):
        if not position:
            position = (
                self.position[0] + self.width / 2,
                self.position[1] + self.height / 2
            )
        position = self.geog.get_available_position_closest_to(self,
            position)

        actor.set_position(position)
        self.actors[actor.actor_id] = actor
        actor.room = self
        if actor.visible:
            self.visibility_grid.add_actor(actor)
        if actor.vision_distance:
            self.visibility_grid.register_listener(actor)

    def remove_actor(self, actor):
        self.actors.pop(actor.actor_id)
        self.save_manager.queue_actor_remove(actor)
        actor._kill_move_gthread()
        actor.room = Null()
        if actor.visible:
            self.visibility_grid.remove_actor(actor)
        if actor.vision_distance:
            self.visibility_grid.unregister_listener(actor)

    def _send_actor_update(self, actor):
        if actor.visible:
            self.visibility_grid.send_update_actor(actor)
        self.send_to_admins("actor_update", **actor.internal())

    def send_to_admins(self, update_id, **kwargs):
        if self.area and self.area.node:
            self.area.node.server.send_to_admins(update_id,
                **kwargs)

    def _send_update(self, actor, update_id, **kwargs):
        self.visibility_grid.send_update_event(actor, update_id, **kwargs)

    def player_exit_to_area(self, actor, door):
        self.remove_actor(actor)
        self.area.node.players.pop(actor.player.username)
        actor.path.set_position(door.exit_position)
        self.area.node.save_manager.update_player_location(actor.player,
            door.exit_area_id, door.exit_room_id)
        for docked in actor.docked.values():
            self.remove_actor(docked)
        transport = [actor] + actor.docked.values()
        self.area.node.move_actors_to_limbo(door.exit_area_id,
            door.exit_room_id, transport)
        response = self.area.node.master.player_moves_area(
            actor.player.username)
        actor._update("moved_node", **response)
        actor._update("disconnect")
        actor.running = False

    def actor_exit_to_area(self, actor, door):
        self.remove_actor(actor)
        actor.path.set_position(door.exit_position)
        for docked in actor.docked.values():
            self.remove_actor(docked)
        transport = [actor] + actor.docked.values()
        self.area.node.move_actors_to_limbo(door.exit_area_id,
            door.exit_room_id, transport)
        response = self.area.node.master.actor_moves_area(
            door.exit_area_id)
        actor.running = False

    def actor_exit_to_room(self, actor, door):
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
        return self.find_actors(actor_type="door")

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
        for door in self.all_doors():
            if door.exit_room_id == room_id:
                return True
        return False

    def actor_said(self, actor, msg):
        for heard in self.actors.values():
            heard.actor_heard(actor, msg)

    def create_actor(self, actor_type, actor_script, position=None,
            actor_id=None, name="", visible=True, visible_to_all=False,
            parents=None, **state):
        actor = Actor(actor_id)
        actor.actor_type = actor_type
        actor.model_type = actor_type
        actor.name = name
        actor.state.update(state)
        actor.visible = visible
        actor.visible_to_all = visible_to_all
        actor.parents = parents or []
        self.put_actor(actor, position)
        actor.load_script(actor_script)
        if "created" in actor.script:
            actor.script.created(actor)
        actor.kick()
        return actor

    def player_actors(self):
        for actor in self._iter_actors():
            if issubclass(actor.__class__, PlayerActor):
                yield actor

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

    def send_message(self, from_actor_id, actor_id, room_id, area_id, message):
        self.area.node.send_message(from_actor_id, actor_id, room_id, area_id,
            message)

    def has_active_players(self):
        for actor in self.player_actors():
            if actor.running == True:
                return True
        if self.area.node and self.area.node.admins:
            return True
        return False

    def has_active_actors(self):
        for actor in self._iter_actors():
            if actor.running == True:
                return True
        return False
