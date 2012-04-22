
from room import Room

class Area(object):
    def __init__(self):
        self.actors = dict()
        self.rooms = dict()

    def actor_enters(self, actor, room_id, door_id):
        self.rooms[room_id].actor_enters(actor, door_id)

    def actor_exits(self, actor):
        self.rooms[actor.room.room_id].actor_exits(actor)
