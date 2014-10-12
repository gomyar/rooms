
import json
import os

from rooms.room import Room
from rooms.room import RoomObject
from rooms.room import Tag
from rooms.room import Door
from rooms.position import Position
from rooms.visibility import Visibility
from rooms.visibility import Area
from rooms.gridvision import GridVision


class FileMapSource(object):
    def __init__(self, dirpath):
        self.dirpath = dirpath

    def load_map(self, map_id):
        filepath = os.path.join(self.dirpath, "%s.json" % (map_id,))
        return json.loads(open(filepath).read())


class RoomFactory(object):
    POS_TOPLEFT = "relative_topleft"
    POS_ABS = "absolute"
    DEFAULT_GRIDSIZE = 10

    def __init__(self, map_source, node):
        self.map_source = map_source
        self.node = node
        self.origin = Position(0, 0)
        self.positioning = RoomFactory.POS_ABS

    def create(self, game_id, room_id):
        map_id, map_room_id = room_id.split('.')
        map_json = self.load_map(map_id)
        self.positioning = map_json.get("positioning", RoomFactory.POS_ABS)
        if map_room_id not in map_json['rooms']:
            raise Exception("No room %s in map %s" % (map_room_id, map_id))
        return self._create_room(map_json['rooms'][map_room_id], game_id,
            room_id)

    def load_map(self, map_id):
        return self.map_source.load_map(map_id)

    def _create_room(self, room_json, game_id, room_id):
        room = Room(game_id, room_id, self._create_pos(room_json['topleft']),
            self._create_pos(room_json['bottomright']), self.node)
        if self.positioning == RoomFactory.POS_TOPLEFT:
            self.origin = self._create_pos(room_json['topleft'])
        for map_object_json in room_json['room_objects']:
            room.room_objects.append(self._create_object(map_object_json))
        for door_json in room_json['doors']:
            room.doors.append(self._create_door(door_json))
        for tag_json in room_json['tags']:
            room.tags.append(self._create_tag(tag_json))
        room.visibility = self._create_visibility(room,
            room_json.get('visibility', {}))
        return room

    def _create_visibility(self, room, visibility_json):
        return GridVision(room, visibility_json.get('gridsize',
            RoomFactory.DEFAULT_GRIDSIZE))

    def _create_door(self, door_json):
        return Door(door_json['exit_room_id'],
            self._create_pos(door_json['enter_position']),
            self._create_pos(door_json['exit_position']))

    def _create_object(self, map_object_json):
        return RoomObject(map_object_json['object_type'],
            self._create_pos(map_object_json['topleft']),
            self._create_pos(map_object_json['bottomright']))

    def _create_tag(self, tag_json):
        return Tag(tag_json['tag_type'], self._create_pos(tag_json['position']),
            tag_json['data'])

    def _create_pos(self, pos_json):
        return Position(pos_json['x'] + self.origin.x,
            pos_json['y'] + self.origin.y,
            pos_json.get('z', 0) + self.origin.z)
