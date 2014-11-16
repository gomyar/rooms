
from rooms.position import Position
from rooms.actor import Actor
from rooms.gridvision import GridVision

import logging
log = logging.getLogger("rooms.room")


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
    def __init__(self, object_type, topleft, bottomright):
        self.object_type = object_type
        self.topleft = topleft
        self.bottomright = bottomright

    def __repr__(self):
        return "<RoomObject %s at %s/%s>" (self.object_type, self.topleft,
            self.bottomright)


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

    def create_actor(self, actor_type, script_name, player=None, position=None):
        script = self.node.scripts[script_name]
        actor = self.node.container.create_actor(self, actor_type, script,
            player.username if player else None)
        actor.script.call("created", actor)
        actor.kick()
        self.put_actor(actor, position)
        return actor

    def put_actor(self, actor, position=None):
        self.actors[actor.actor_id] = actor
        actor.room = self
        actor._set_position(position or actor.position)
        actor.kick()
        self.vision.add_actor(actor)
        self.actor_added(actor)

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
        split_path = self._split_path(path, self.vision.gridsize)
        return split_path

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

    def actor_state_changed(self, actor):
        if actor.actor_id in self.actors:
            self.node.actor_state_changed(self, actor)
        else:
            log.warning("Actor not in room but state changed sent: %s", actor)

    def actor_vector_changed(self, actor, previous_vector):
        if actor.actor_id in self.actors:
            self.node.actor_vector_changed(self, actor, previous_vector)
        else:
            log.warning("Actor not in room but vector update sent: %s", actor)

    def actor_added(self, actor):
        if actor.actor_id in self.actors:
            self.node.actor_added(self, actor)
        else:
            log.warning("Actor not in room but actor added sent: %s", actor)

    def actor_becomes_visible(self, actor):
        if actor.actor_id in self.actors:
            self.node.actor_becomes_visible(self, actor)
        else:
            log.warning("Actor not in room but actor visible sent: %s", actor)

    def actor_becomes_invisible(self, actor):
        if actor.actor_id in self.actors:
            self.node.actor_becomes_invisible(self, actor)
        else:
            log.warning("Actor not in room but actor invisible sent: %s", actor)

    def get_door(self, exit_room_id=None):
        for door in self.doors:
            if door.exit_room_id == exit_room_id:
                return door
        return None

    def actor_enters(self, actor, door):
        self.move_actor_room(actor, door.exit_room_id, door.exit_position)

    def move_actor_room(self, actor, room_id, exit_position):
        self.node.move_actor_room(actor, self.game_id, room_id, exit_position)

    def remove_actor(self, actor):
        self.actors.pop(actor.actor_id)
        actor._kill_gthreads()
        actor.room = None
        self.node.actor_removed(self, actor)

    def find_tags(self, tag_id):
        return [tag for tag in self.tags if tag.tag_type.startswith(tag_id)]

    def object_at(self, position):
        for room_object in self.room_objects:
            if position.is_within(room_object.topleft, room_object.bottomright):
                return True
        return False
