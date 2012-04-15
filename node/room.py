

class Room:
    def __init__(self, room_id=None, width=50, height=50):
        self.room_id = room_id
        self.width = width
        self.height = height
        self.map_objects = []
        self.doors = dict()
        self.actors = dict()

    def __eq__(self, rhs):
        return rhs and self.__dict__ == rhs.__dict__

    def actor_enters(self, actor, door_id):
        self.actors[actor.player_id] = actor
        actor.room = self

    def actor_exits(self, actor):
        self.actors.pop(actor.player_id)
        actor.room = None
