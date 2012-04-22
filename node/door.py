
from actor import Actor

class Door(Actor):
    def __init__(self, door_id=None, position=None, exit_room=None,
            exit_door_id=None):
        super(Door, self).__init__(door_id)
        self.exit_room = exit_room
        self.exit_door_id = exit_door_id
        self.position = position

    def __eq__(self, rhs):
        return rhs and self.exit_room == rhs.exit_room and \
            self.exit_door_id == rhs.exit_door_id and \
            self.position == rhs.position

    def __repr__(self):
        return "<Door at %s to %s through %s>" % (self.position,
            self.exit_room, self.exit_door_id)
