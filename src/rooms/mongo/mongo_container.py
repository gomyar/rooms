
import simplejson

from pymongo import Connection
from pymongo.helpers import bson

from rooms.room_container import RoomContainer

from rooms.container import _decode
from rooms.container import _encode
from rooms.player import Player


class MongoRoomContainer(RoomContainer):
    def __init__(self, area, mongo_container):
        super(MongoRoomContainer, self).__init__(area)
        self.mongo_container = mongo_container

    def load_room(self, room_id):
        return self.load_room_from_mongo(room_id)

    def save_room(self, room_id, room):
        return self.save_room_to_mongo(room)

    def save_room_to_mongo(self, room):
        rooms_db = self.mongo_container._mongo_connection.rooms_db
        _save_object(room, rooms_db.rooms)
        return str(room._id)

    def load_room_from_mongo(self, room_id):
        rooms_db = self.mongo_container._mongo_connection.rooms_db
        return _load_object(room_id, rooms_db.rooms)


def _save_object(obj, collection):
    encoded_str = simplejson.dumps(obj, default=_encode, indent="    ")
    encoded_dict = simplejson.loads(encoded_str)
    if hasattr(obj, "_id"):
        encoded_dict['_id'] = obj._id
    obj_id = collection.save(encoded_dict)
    obj._id = obj_id
    return str(obj_id)

def _load_object(obj_id, collection):
    obj_dict = collection.find_one(bson.ObjectId(obj_id))
    db_id = obj_dict.pop('_id')
    obj_str = simplejson.dumps(obj_dict)
    obj = simplejson.loads(obj_str, object_hook=_decode)
    obj._id = db_id
    return obj



class MongoContainer(object):
    def __init__(self, host='localhost', port=27017):
        self.host = host
        self.port = port
        self._mongo_connection = None

    def init_mongo(self):
        self._mongo_connection = Connection(self.host, self.port)

    def load_area(self, area_id):
        rooms_db = self._mongo_connection.rooms_db
        area = _load_object(area_id, rooms_db.areas)
        area.rooms = MongoRoomContainer(area, self)
        area.rooms._room_map = area._room_map
        return area

    def save_area(self, area):
        rooms_db = self._mongo_connection.rooms_db
        _save_object(area, rooms_db.areas)
        for room in area.rooms._rooms.values():
            area.rooms.save_room_to_mongo(room)

    def list_all_areas_for(owner_id):
        rooms_db = self._mongo_connection.rooms_db
        areas = rooms_db.areas.find({ 'owner_id': owner_id },
            fields=['area_name'])
        return map(lambda a: dict(area_name=a['area_name'],
            area_id=str(a['_id'])), areas)

    def save_game(self, game):
        rooms_db = self._mongo_connection.rooms_db
        _save_object(game, rooms_db.games)

    def get_or_create_player(self, player_id):
        rooms_db = self._mongo_connection.rooms_db
        player = rooms_db.players.find_one(username=player_id)
        if not player:
            player = Player(player_id)
            _save_object(player, rooms_db.players)
        else:
            player = _load_object(str(player['_id']), rooms_db.players)
        return player

    def save_player(self, player):
        rooms_db = self._mongo_connection.rooms_db
        _save_object(player, rooms_db.players)
