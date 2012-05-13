
from actor import Actor
from actor import FACING_NORTH
from actor import FACING_SOUTH
from actor import FACING_EAST
from actor import FACING_WEST


open_dirs = {
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
        self.exit_room = exit_room
        self.exit_door_id = exit_door_id
        self.set_position(position)
        self.opens_direction = FACING_NORTH

    def __eq__(self, rhs):
        return rhs and self.exit_room == rhs.exit_room and \
            self.exit_door_id == rhs.exit_door_id

    def __repr__(self):
        return "<Door at %s, %s to %s through %s>" % (self.x(), self.y(),
            self.exit_room, self.exit_door_id)

    def external(self):
        d = super(Door, self).external()
        d['opens_direction'] = self.opens_direction
        return d
