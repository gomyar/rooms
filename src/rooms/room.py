
from rooms.position import Position
from rooms.actor import Actor


class State(dict):
    def __init__(self, actor):
        super(State, self).__init__()
        self.__dict__['actor'] = actor

    def __getattr__(self, name):
        return self.get(name, None)

    def __setattr__(self, name, value):
        self[name] = value


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
        for actor in self.actors.values():
            actor.kick()

    def create_actor(self, actor_type, script_name, player=None):
        script = self.node.scripts[script_name]
        actor = self.node.container.create_actor(self, actor_type, script,
            player.username if player else None)
        actor.script.call("created", actor)
        actor.kick()
        self.put_actor(actor)
        return actor

    def put_actor(self, actor, position=None):
        self.actors[actor.actor_id] = actor
        actor.room = self
        if position:
            actor.position = position

    def player_actors(self):
        return [a for a in self.actors.values() if a.is_player]

    def find_path(self, from_pos, to_pos):
        return self.geography.find_path(self, from_pos, to_pos)

    def actor_update(self, actor):
        self.node.actor_update(self, actor)

    def get_door(self, exit_room_id=None):
        for door in self.doors:
            if door.exit_room_id == exit_room_id:
                return door
        return None

    def actor_enters(self, actor, door):
        self.node.move_actor_room(actor, self.game_id, door.exit_room_id,
            door.exit_position)

    def remove_actor(self, actor):
        self.actors.pop(actor.actor_id)
        actor.room = None
