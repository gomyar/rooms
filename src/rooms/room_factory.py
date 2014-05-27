
import json
import os

from rooms.room import Room
from rooms.room import RoomObject
from rooms.room import Tag
from rooms.position import Position


class FileMapSource(object):
    def __init__(self, dirpath):
        self.dirpath = dirpath

    def load_map(self, map_id):
        filepath = os.path.join(self.dirpath, "%s.json" % (map_id,))
        return json.loads(open(filepath).read())


class RoomFactory(object):
    def __init__(self, map_source, node):
        self.map_source = map_source
        self.node = node

    def create(self, game_id, room_id):
        map_id, map_room_id = room_id.split('.')
        map_json = self.map_source.load_map(map_id)
        return self._create_room(map_json['rooms'][map_room_id], game_id,
            room_id)

    def _create_room(self, room_json, game_id, room_id):
        room = Room(game_id, room_id, self._create_pos(room_json['topleft']),
            self._create_pos(room_json['bottomright']), self.node)
        for map_object_json in room_json['room_objects']:
            room.room_objects.append(self._create_object(map_object_json))
        for tag_json in room_json['tags']:
            room.tags.append(self._create_tag(tag_json))
        return room

    def _create_object(self, map_object_json):
        return RoomObject(map_object_json['object_type'],
            self._create_pos(map_object_json['topleft']),
            self._create_pos(map_object_json['bottomright']))

    def _create_tag(self, tag_json):
        return Tag(tag_json['tag_type'], self._create_pos(tag_json['position']),
            tag_json['data'])

    def _create_pos(self, pos_json):
        return Position(pos_json['x'], pos_json['y'], pos_json['z'])
