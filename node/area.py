
class Area:
    def __init__(self):
        self.actors = dict()
        self.rooms = dict()

    def actor_enters(actor, room_id, door_id):
        self.area.rooms[room_id].actor_enters(actor, door_id)

    def actor_exits(actor):
        self.area.rooms[actor.room.room_id].actor_exits(actor)
