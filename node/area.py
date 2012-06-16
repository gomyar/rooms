
import eventlet

from room import Room
from door import Door
from door import infer_direction

from npc_actor import NpcActor

class Area(object):
    def __init__(self):
        self.area_name = None
        self.entry_point_room_id = None
        self.entry_point_door_id = None
        self.actors = dict()
        self.rooms = dict()
        self.owner_id = ""
        self.game_script = None

    def player_joined_instance(self, actor, room_id):
        self.rooms[room_id].player_joined_instance(actor)

    def actor_left_instance(self, actor):
        self.rooms[actor.room.room_id].actor_left_instance(actor)

    def add_npc(self, npc_actor, room_id):
        self.actors[npc_actor.actor_id] = npc_actor
        self.player_joined_instance(npc_actor, room_id)

    def kickoff_npcs(self, instance):
        self.game_script.kickoff(self)
        npcs = [npc for npc in self.actors.values() if type(npc) is NpcActor]
        for npc in npcs:
            npc.instance = instance
            eventlet.spawn(npc.kickoff)

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
        door1.opens_direction = infer_direction(room1_position,
            room2_position)
        door2.opens_direction = infer_direction(room2_position,
            room1_position)
