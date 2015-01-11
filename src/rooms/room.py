
from rooms.position import Position
from rooms.actor import Actor
from rooms.gridvision import GridVision

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
    def __init__(self, object_type, topleft, bottomright, info):
        self.object_type = object_type
        self.topleft = topleft
        self.bottomright = bottomright
        self.info = info

    def __repr__(self):
        return "<RoomObject %s at %s/%s>" % (self.object_type, self.topleft,
            self.bottomright)

    @property
    def center(self):
        return Position(
            self.topleft.x + (self.bottomright.x - self.topleft.x) / 2,
            self.topleft.y + (self.bottomright.y - self.topleft.y) / 2,
            self.topleft.z + (self.bottomright.z - self.topleft.z) / 2,
        )


class Door(object):
    def __init__(self, exit_room_id, enter_position, exit_position):
        self.exit_room_id = exit_room_id
        self.enter_position = enter_position
        self.exit_position = exit_position

    def __repr__(self):
        return "<Door to %s at %s>" % (self.exit_room_id, self.enter_position)


class Room(object):
    def __init__(self, game_id, room_id, topleft, bottomright, node):
        self.game_id = game_id
        self.room_id = room_id
        self.topleft = topleft
        self.bottomright = bottomright
        self.geography = None
        self.actors = dict()
        self.room_objects = []
        self.doors = []
        self.tags = []
        self.node = node
        self.online = True
        self.vision = GridVision(self, self.width)
        self.state = dict()
        self.info = dict()
        self.item_registry = None

    def __repr__(self):
        return "<Room %s %s>" % (self.game_id, self.room_id)

    @property
    def width(self):
        return self.bottomright.x - self.topleft.x

    @property
    def height(self):
        return self.bottomright.y - self.topleft.y

    @property
    def center(self):
        return Position(
            self.topleft.x + (self.bottomright.x - self.topleft.x) / 2,
            self.topleft.y + (self.bottomright.y - self.topleft.y) / 2,
            self.topleft.z + (self.bottomright.z - self.topleft.z) / 2,
        )

    def kick(self):
        log.debug("Kicking room (%s actors)", len(self.actors))
        for actor in self.actors.values():
            actor.kick()

    def create_actor(self, actor_type, script_name, username=None,
            position=None, state=None, visible=True, parent_id=None):
        script = self.node.scripts[script_name]
        actor = self.node.container.create_actor(self, actor_type, script,
            username=username, state=state, visible=visible,
            parent_id=parent_id)
        actor.script.call("created", actor)
        actor.kick()
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
        x = min(self.bottomright.x, max(self.topleft.x, x))
        y = min(self.bottomright.y, max(self.topleft.y, y))
        z = min(self.bottomright.z, max(self.topleft.z, z))
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

    def move_actor_room(self, actor, room_id, exit_position):
        # remove docked
        # remove actor
        # save all docked
        # save actor
        docked = list(actor.docked_actors)
        self.remove_actor(actor)
        for child in docked:
            self.remove_actor(child)
        for child in docked:
            self.node.save_actor_to_other_room(room_id, exit_position, child)
        self.node.save_actor_to_other_room(room_id, exit_position, actor)
        if actor.actor_id in self.vision.actor_queues:
            for queue in self.vision.actor_queues[actor.actor_id]:
                queue.put({"command": "move_room", "room_id": room_id})

    def remove_actor(self, actor):
        if actor._follow_event:
            actor._follow_event.set_exception(TargetLost())
        self.actors.pop(actor.actor_id)
        actor._kill_gthreads()
        actor.room = None
        if actor.docked_with:
            actor.docked_with.docked_actors.remove(actor)
            actor.docked_with = None
        self.vision.actor_removed(actor)

    def find_tags(self, tag_id):
        return [tag for tag in self.tags if tag.tag_type.startswith(tag_id)]

    def object_at(self, position):
        for room_object in self.room_objects:
            if position.is_within(room_object.topleft, room_object.bottomright):
                return True
        return False

    def send_message(self, message_type, position, **data):
        self.vision.send_message(message_type, position, data)

    def find_actors(self, actor_type=None, state=None):
        def test(actor):
            t = not actor_type or actor_type == actor.actor_type
            s = not state or \
                all(item in actor.state.items() for item in state.items())
            return t and s
        return [a for a in self.actors.values() if test(a)]
