
from actor import Actor
from actor import FACING_NORTH
from actor import FACING_SOUTH
from actor import FACING_EAST
from actor import FACING_WEST


open_dirs = {
    (0, 0): FACING_EAST,
    (-1, -1): FACING_EAST,
    (-1, 1): FACING_EAST,
    (1, -1): FACING_EAST,
    (1, 1): FACING_EAST,
    (1, 0): FACING_EAST,
    (0, 1): FACING_SOUTH,
    (-1, 0): FACING_WEST,
    (0, -1): FACING_NORTH,
}


def infer_direction(from_position, to_position):
    w = to_position[0] - from_position[0]
    w = w / abs(w) if w else 0
    h = to_position[1] - from_position[1]
    h = h / abs(h) if h else 0
    return open_dirs[w, h]


class Door(Actor):
    def __init__(self, door_id=None, position=(0, 0), exit_room=None,
            exit_door_id=None):
        super(Door, self).__init__(door_id)
        self.exit_room_id = exit_room.room_id if exit_room else None
        self.exit_door_id = exit_door_id
        self.set_position(position)
        self.opens_direction = FACING_NORTH

    @property
    def exit_room(self):
        return self.room.area.rooms[self.exit_room_id]

    def __eq__(self, rhs):
        return rhs and type(rhs) is Door \
            and self.exit_room_id == rhs.exit_room_id \
            and self.exit_door_id == rhs.exit_door_id

    def __repr__(self):
        return "<Door at %s, %s to %s through %s>" % (self.x(), self.y(),
            self.exit_room_id, self.exit_door_id)

    def external(self):
        return dict(actor_id=self.actor_id, actor_type=type(self).__name__,
            path=self.path.path, speed=self.speed,
            model_type=self.model_type,
            opens_direction=self.opens_direction)
