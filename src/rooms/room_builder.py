
import json
import os

from rooms.room import Room
from rooms.room import RoomObject
from rooms.room import Tag
from rooms.room import Door
from rooms.position import Position
from rooms.vision import Vision


class FileMapSource(object):
    def __init__(self, dirpath):
        self.dirpath = dirpath

    def load_map(self, map_id):
        filepath = os.path.join(self.dirpath, "%s.json" % (map_id,))
        return json.loads(open(filepath).read())


class SimpleRoomBuilder(object):
    def create(self, game_id, room_id):
        return Room(game_id, room_id, None)


class RoomBuilder(object):
    POS_ABS = "absolute"
    DEFAULT_GRIDSIZE = 25
    DEFAULT_LINKSIZE = 2

    def __init__(self, map_source, node):
        self.map_source = map_source
        self.node = node
        self.origin = Position(0, 0)

    def create(self, game_id, room_id):
        map_id, _ = room_id.split('.')
        map_json = self.load_map(map_id)
        if room_id not in map_json['rooms']:
            raise Exception("No room %s in map %s" % (room_id, map_id))
        return self._create_room(map_json['rooms'][room_id], game_id,
            room_id)

    def load_map(self, map_id):
        return self.map_source.load_map(map_id)

    def _create_room(self, room_json, game_id, room_id):
        room = Room(game_id, room_id, self.node)
        room.info = room_json.get('info', {})
        room.position = self._create_pos(room_json['position'])
        room.width = room_json.get('width', 0)
        room.height = room_json.get('height', 0)

        for map_object_json in room_json['room_objects']:
            room.room_objects.append(self._create_object(map_object_json))
        for door_json in room_json['doors']:
            room.doors.append(self._create_door(door_json))
        for tag_json in room_json['tags']:
            room.tags.append(self._create_tag(tag_json))
        room.vision = self._create_vision(room,
            room_json.get('vision', {}))
        return room

    def _create_vision(self, room, vision_json):
        return Vision(room)

    def _create_door(self, door_json):
        if 'exit_position' in door_json:
            exit_position = self._create_pos(door_json['exit_position'])
        else:
            exit_position = None
        return Door(door_json['exit_room_id'],
            self._create_pos(door_json['position']),
            exit_position)

    def _create_object(self, map_object_json):
        room_object = RoomObject(map_object_json['object_type'],
            self._create_pos(map_object_json['position']),
            map_object_json.get('width', 0),
            map_object_json.get('height', 0),
            map_object_json.get('depth', 0),
            map_object_json.get('passable', False))
        room_object.info = map_object_json.get('info', {})
        room_object.facing = map_object_json.get('facing', 0)
        return room_object

    def _create_tag(self, tag_json):
        return Tag(tag_json['tag_type'], self._create_pos(tag_json['position']),
            tag_json['data'])

    def _create_pos(self, pos_json):
        return Position(**pos_json)
