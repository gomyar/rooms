
from actor import Actor

class Door(Actor):
    def __init__(self, door_id=None, position=(0, 0), exit_room=None,
            exit_door_id=None):
        super(Door, self).__init__(door_id)
        self.exit_room = exit_room
        self.exit_door_id = exit_door_id
        self.set_position(position)

    def __eq__(self, rhs):
        return rhs and self.exit_room == rhs.exit_room and \
            self.exit_door_id == rhs.exit_door_id

    def __repr__(self):
        return "<Door at %s, %s to %s through %s>" % (self.x(), self.y(),
            self.exit_room, self.exit_door_id)
