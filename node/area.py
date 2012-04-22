
from room import Room
from door import Door

class Area(object):
    def __init__(self):
        self.area_name = None
        self.entry_point_room_id = None
        self.entry_point_door_id = None
        self.actors = dict()
        self.rooms = dict()
        self.owner_id = ""

    def actor_enters(self, actor, room_id, door_id):
        self.rooms[room_id].actor_enters(actor, door_id)

    def actor_exits(self, actor):
        self.rooms[actor.room.room_id].actor_exits(actor)

    def create_door(self, room1, room2, room1_position, room2_position):
        door1_id = "door_%s_%s_%s" % (room2.room_id, room1_position[0],
            room1_position[1])
        door2_id = "door_%s_%s_%s" % (room1.room_id, room2_position[0],
            room2_position[1])
        door1 = Door(door1_id, room1_position, room2, door2_id)
        door2 = Door(door2_id, room2_position, room1, door1_id)
        room1.actors[door1_id] = door1
        room2.actors[door2_id] = door2
        door1.room = room1
        door2.room = room2
        self.actors[door1_id] = door1
        self.actors[door2_id] = door2
