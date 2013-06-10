
from rooms.room import Room
from rooms.door import Door
from rooms.door import infer_direction
from rooms.room_container import RoomContainer

from rooms.npc_actor import NpcActor
from rooms.player_actor import PlayerActor
from rooms.script_wrapper import Script

from rooms.geography.astar import PointMap
from rooms.geography.astar import Point
from rooms.geography.astar import AStar

class Area(object):
    def __init__(self):
        self.area_id = None
        self.entry_point_door_id = None
        self.rooms = dict()
        self.owner_id = ""
        self.point_map = dict()
        self.room_points = dict()
        self.game = None
        self.node = None
        self.icicle_map = dict()

    def rebuild_area_map(self):
        self.point_map = PointMap()
        for room_id in self.rooms:
            room = self.rooms[room_id]
            center = room.center()
            self.room_points[center] = room_id
            point = Point(*center)
            self.point_map[center] = point
            point._connected = [door.exit_room.center() for \
                door in room.all_doors()]
        for point in self.point_map._points.values():
            point._connected = [self.point_map[p] for p in point._connected]

    def find_path_to_room(self, from_room_id, to_room_id):
        from_room_center = self.rooms[from_room_id].center()
        to_room_center = self.rooms[to_room_id].center()
        path = AStar(self.point_map).find_path(self.point_map[from_room_center],
            self.point_map[to_room_center])
        return [self.room_points[p] for p in path]

    def load_script(self, classname):
        self.game_script = Script(classname)

    def put_room(self, room, position):
        self.rooms[room.room_id] = room
        room.area = self
        room.position = position

    def actor_enters_room(self, room, actor, door_id=None):
        if type(actor) is PlayerActor and self.game_script and \
                self.game_script.has_method('player_enters_room'):
            self.game_script.call_method('player_enters_room', room, actor)

    def create_room(self, room_id, position, width=50, height=50,
            description=None, visibility_grid_gridsize=100):
        room = Room(room_id, width, height, description,
            visibility_grid_gridsize=visibility_grid_gridsize)
        self.put_room(room, position)
        return room

    def create_door(self, room1, room2, room1_position=None,
            room2_position=None, door1_visible_to_all=False,
            door2_visible_to_all=False):
        if not room1_position:
            room1_position = room1.calculate_door_position(room2)
        if not room2_position:
            room2_position = room2.calculate_door_position(room1)
        door1_id = "door_%s_%s_%s" % (room2.room_id, room1_position[0],
            room1_position[1])
        door2_id = "door_%s_%s_%s" % (room1.room_id, room2_position[0],
            room2_position[1])
        door1 = Door(door1_id, room1_position, room2.room_id, None)
        door2 = Door(door2_id, room2_position, room1.room_id, None)
        door2.exit_door_id = door1.actor_id
        door2.exit_position = room1_position
        door1.exit_position = room2_position
        door1.exit_door_id = door2.actor_id
        room1.actors[door1.actor_id] = door1
        room2.actors[door2.actor_id] = door2
        door1.room = room1
        door2.room = room2
        door1.opens_direction = infer_direction(room1_position,
            room2_position)
        door2.opens_direction = infer_direction(room2_position,
            room1_position)
        door1.visible_to_all = door1_visible_to_all
        door2.visible_to_all = door2_visible_to_all
        door1.name = room2.description
        door2.name = room1.description
        if room1.area != room2.area:
            door1.exit_area_id = room2.area.area_id
            door2.exit_area_id = room1.area.area_id

    def _find_player(self, player_id):
        for room in self.rooms.values():
            for actor in room.actors.values():
                if actor.actor_id == player_id:
                    return actor
        return None
