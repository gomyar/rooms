
import gevent
from rooms.position import Position
from rooms.actor import Actor
from rooms.actor import search_actor_test
from rooms.vision import Vision
from rooms.script import NullScript
from rooms.script import load_script
from rooms.actor_loader import ActorLoader

import logging
log = logging.getLogger("rooms.room")


class TargetLost(Exception):
    pass


class Tag(object):
    def __init__(self, tag_type, position, data=None):
        self.tag_type = tag_type
        self.position = position
        self.data = data or {}

    def __repr__(self):
        return "<Tag %s (%s)>" % (self.tag_type, self.position)

    def __eq__(self, rhs):
        return rhs and type(rhs) is Tag and self.tag_type == rhs.tag_type and \
            self.position == rhs.position and \
            self.data == rhs.data


class RoomObject(object):
    def __init__(self, object_type, position, width=0, height=0, depth=0):
        self.object_type = object_type
        self.position = position
        self.width = width
        self.height = height
        self.depth = depth
        self.info = dict()

    def __repr__(self):
        return "<RoomObject %s at %s w:%s h:%s>" % (
            self.object_type, self.position, self.width, self.height)

    @property
    def center(self):
        return self.position

    @property
    def topleft(self):
        return self.position.add_coords(-self.width / 2.0, -self.height / 2.0,
                                        -self.depth / 2.0)

    @property
    def bottomright(self):
        return self.position.add_coords(self.width / 2.0, self.height / 2.0,
                                        self.depth / 2.0)


class Door(object):
    def __init__(self, exit_room_id, position, exit_position):
        self.exit_room_id = exit_room_id
        self.position = position
        self.exit_position = exit_position

    def __repr__(self):
        return "<Door to %s at %s>" % (self.exit_room_id, self.position)


class Room(object):
    def __init__(self, game_id, room_id, node, script=None):
        self.game_id = game_id
        self.room_id = room_id
        self.node = node
        self.script = script or NullScript()
        self.initialized = False
        self.position = Position(0, 0)
        self.width = 0
        self.height = 0
        self.depth = 0
        self.geography = None
        self.actors = dict()
        self.room_objects = []
        self.doors = []
        self.tags = []
        self.online = True
        self.vision = Vision(self)
        self.state = dict()
        self.info = dict()
        self.actor_loader = ActorLoader(self)
        self._actorload_gthread = None
        self._node_name = None

    def __repr__(self):
        return "<Room %s %s>" % (self.game_id, self.room_id)

    @property
    def item_registry(self):
        return self.node.container.item_registry

    @property
    def node_name(self):
        return self._node_name

    def start(self):
        self.start_actorloader()
        self.start_actors()

    def start_actorloader(self):
        self.actor_loader.start()

    def start_actors(self):
        log.debug("Kicking room (%s actors)", len(self.actors))
        for actor in self.actors.values():
            actor.kick()

    def stop(self):
        self.stop_actors()
        self.stop_actorloader()

    def stop_actorloader(self):
        self.actor_loader.stop()

    def stop_actors(self):
        for actor in self.actors.values():
            actor.stop()

    @property
    def topleft(self):
        return self.position.add_coords(-self.width / 2.0, -self.height / 2.0,
                                        -self.depth / 2.0)

    @property
    def bottomright(self):
        return self.position.add_coords(self.width / 2.0, self.height / 2.0,
                                        self.depth / 2.0)

    def coords(self, x1, y1, x2, y2):
        self.position = Position(x1 + (x2 - x1) / 2, y1 + (y2 - y1) / 2)
        self.width = x2 - x1
        self.height = y2 - y1

    def create_actor(self, actor_type, script_name=None, username=None,
            position=None, state=None, visible=True, parent_id=None):
        if script_name:
            script = load_script(script_name)
        else:
            script = NullScript()
        actor = self.node.container.create_actor(self, actor_type, script,
            username=username, state=state, visible=visible,
            parent_id=parent_id, position=position)
        actor.script.call("created", actor)
        actor.initialized = True
        self.node.container.update_actor(actor, initialized=True)
        self.put_actor(actor, position)
        return actor

    def put_actor(self, actor, position=None):
        self.actors[actor.actor_id] = actor
        if actor._docked_with:
            parent = self.actors[actor._docked_with]
            actor.docked_with = parent
            parent.docked_actors.add(actor)
        actor.room = self
        actor._set_position(position or actor.position)
        actor.kick()
        self.vision.add_actor(actor)

    def _correct_position(self, position):
        x, y, z = position.x, position.y, position.z
        x = min(self.width / 2, max(-self.width / 2, x))
        y = min(self.height / 2, max(-self.height / 2, y))
        z = min(self.depth / 2, max(-self.depth / 2, z))
        return Position(x, y, z)

    def player_actors(self):
        return [a for a in self.actors.values() if a.is_player]

    def find_path(self, from_pos, to_pos):
        path = self.geography.find_path(self, self._correct_position(from_pos),
            self._correct_position(to_pos))
        return path

    def _split_path(self, path, max_length):
        split_path = []
        from_point = path[0]
        for to_point in path[1:]:
            split_path.extend(self._split_points(from_point, to_point,
                max_length) + [to_point])
        return split_path

    def _split_points(self, from_point, to_point, max_length):
        if abs(to_point.x - from_point.x) > max_length or \
                abs(to_point.y - from_point.y) > max_length:
            halfway = Position((to_point.x + from_point.x) / 2,
                (to_point.y + from_point.y) / 2)
            return self._split_points(from_point, halfway, max_length) + \
                self._split_points(halfway, to_point, max_length)
        else:
            return [from_point]

    def get_door(self, exit_room_id=None):
        for door in self.doors:
            if door.exit_room_id == exit_room_id:
                return door
        return None

    def actor_enters(self, actor, door):
        self.move_actor_room(actor, door.exit_room_id, door.exit_position)
        # should move all docked actors as well, but may not be able
        # to load them all in the correct order at the other end

    def move_actor_room(self, actor, room_id, exit_position=None):
        self._remove_actor(actor)
        actor._move_undock()
        docked = self._remove_docked(actor)
        for child in docked:
            self.node.save_actor_to_other_room(room_id, actor, exit_position)
        self.node.save_actor_to_other_room(room_id, actor, exit_position)
        if actor.actor_id in self.vision.actor_queues:
            for queue in self.vision.actor_queues[actor.actor_id]:
                queue.put({"command": "move_room", "room_id": room_id})

    def _remove_docked(self, actor):
        docked = list(actor.docked_actors)
        for child in actor.docked_actors:
            docked.extend(self._remove_docked(child))
            self._remove_actor(child)
        return docked

    def _remove_actor(self, actor):
        actor._notify_trackers()
        self.actors.pop(actor.actor_id)
        actor._kill_gthreads()
        actor.room = None
        self.vision.actor_removed(actor)

    def find_tags(self, tag_id):
        return [tag for tag in self.tags if tag.tag_type.startswith(tag_id)]

    def find_room_objects(self, object_type, **kwargs):
        return [obj for obj in self.room_objects if \
            obj.object_type == object_type and
            all(item in obj.info.items() for item in kwargs)]

    def object_at(self, position):
        for room_object in self.room_objects:
            if position.is_within(room_object.topleft, room_object.bottomright):
                return True
        return False

    def send_message(self, message_type, position, **data):
        self.vision.send_message(message_type, position, data)

    def find_actors(self, actor_type=None, state=None, visible=None,
            distance=None, distance_to=None):
        return [a for a in self.actors.values() if \
            search_actor_test(a, actor_type, state, visible, distance,
            distance_to)]
