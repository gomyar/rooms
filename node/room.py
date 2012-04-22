

class Room(object):
    def __init__(self, room_id=None, x=0, y=0, width=50, height=50):
        self.room_id = room_id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.map_objects = []
        self.actors = dict()

    def __eq__(self, rhs):
        return rhs and self.room_id == rhs.room_id

    def __repr__(self):
        return "<Room %s>" % (self.room_id,)

    def actor_enters(self, actor, door_id):
        self.actors[actor.actor_id] = actor
        actor.room = self

    def actor_exits(self, actor):
        self.actors.pop(actor.actor_id)
        actor.room = None
