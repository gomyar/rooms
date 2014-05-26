
from rooms.room import Room
from rooms.room import RoomObject
from rooms.room import Tag
from rooms.position import Position


class RoomFactory(object):
    def __init__(self, map_json, node):
        self.map_json = map_json
        self.node = node

    def create(self, room_id, game_id):
        return self._create_room(self.map_json['rooms'][room_id], game_id,
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
