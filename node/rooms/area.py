
import eventlet

from rooms.room import Room
from rooms.door import Door
from rooms.door import infer_direction
from rooms.room_container import RoomContainer

from rooms.npc_actor import NpcActor
from rooms.player_actor import PlayerActor
from rooms.script_wrapper import Script

class Area(object):
    def __init__(self):
        self.area_name = None
        self.entry_point_room_id = None
        self.entry_point_door_id = None
        self.rooms = RoomContainer(self)
        self.owner_id = ""
        self.game_script = None
        self.player_script = None
        self.instance = None

    def load_script(self, classname):
        self.game_script = Script(classname)

    def player_joined_instance(self, player, room_id):
        if self.player_script:
            player.load_script(self.player_script)
        if self.game_script:
            self.game_script.call_event_method("player_joined_instance", player,
                room_id)
        self.actor_joined_instance(player, room_id)

    def actor_joined_instance(self, actor, room_id):
        self.rooms[room_id].actor_joined_instance(actor)

    def actor_left_instance(self, actor):
        self.rooms[actor.room.room_id].actor_left_instance(actor)

    def add_npc(self, npc_actor, room_id):
        self.actor_joined_instance(npc_actor, room_id)

    def add_room(self, room):
        self.rooms[room.room_id] = room
        room.area = self

    def actor_enters_room(self, room, actor, door_id=None):
        if type(actor) is PlayerActor and self.game_script:
            self.game_script.call_event_method('player_enters_room',
                room, actor)

    def create_door(self, room1, room2, room1_position=None,
            room2_position=None):
        if not room1_position:
            room1_position = room1.calculate_door_position(room2)
        if not room2_position:
            room2_position = room2.calculate_door_position(room1)
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
        door1.opens_direction = infer_direction(room1_position,
            room2_position)
        door2.opens_direction = infer_direction(room2_position,
            room1_position)
