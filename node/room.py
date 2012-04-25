

class Room(object):
    def __init__(self, room_id=None, position=(0, 0), width=50, height=50):
        self.room_id = room_id
        self.position = position
        self.width = width
        self.height = height
        self.map_objects = []
        self.actors = dict()

    def __eq__(self, rhs):
        return rhs and self.room_id == rhs.room_id

    def __repr__(self):
        return "<Room %s>" % (self.room_id,)

    def external(self):
        return dict(room_id=self.room_id, position=self.position,
            width=self.width, height=self.height, map_objects=self.map_objects)

    def actor_enters(self, actor, door_id):
        self.actors[actor.actor_id] = actor
        actor.room = self
        actor.set_position(self.actors[door_id].position())

    def actor_exits(self, actor):
        self.actors.pop(actor.actor_id)
        actor.room = None

    def exit_through_door(self, actor, door_id):
        door = self.actors[door_id]
        self.actor_exits(actor)
        door.exit_room.actor_enters(actor, door.exit_door_id)
