
import simplejson

from pymongo import Connection
from pymongo.helpers import bson

from rooms.room_container import RoomContainer

from rooms.container import Container
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
        rooms_db = self.mongo_container.db()
        self.mongo_container._save_object(room, rooms_db.rooms)
        return str(room._id)

    def load_room_from_mongo(self, room_id):
        rooms_db = self.mongo_container.db()
        return self.mongo_container._load_object(room_id, rooms_db.rooms)


class MongoContainer(object):
    def __init__(self, host='localhost', port=27017, dbname="rooms_db"):
        self.host = host
        self.port = port
        self.dbname = dbname
        self._mongo_connection = None
        self.container = None

    def db(self):
        return getattr(self._mongo_connection, self.dbname)

    def _save_object(self, obj, collection):
        encoded_str = simplejson.dumps(obj, default=self.container._encode,
            indent="    ")
        encoded_dict = simplejson.loads(encoded_str)
        if hasattr(obj, "_id"):
            encoded_dict['_id'] = obj._id
        obj_id = collection.save(encoded_dict)
        obj._id = obj_id
        return str(obj_id)

    def _load_object(self, obj_id, collection):
        obj_dict = collection.find_one(bson.ObjectId(obj_id))
        db_id = obj_dict.pop('_id')
        obj_str = simplejson.dumps(obj_dict)
        obj = simplejson.loads(obj_str, object_hook=self.container._decode)
        obj._id = db_id
        return obj

    def init_mongo(self):
        self._mongo_connection = Connection(self.host, self.port)

    def load_area(self, area_id):
        area = self._load_object(area_id, self.db().areas)
        area.rooms = MongoRoomContainer(area, self)
        area.rooms._room_map = area._room_map
        return area

    def save_area(self, area):
        self._save_object(area, self.db().areas)
        for room in area.rooms._rooms.values():
            area.rooms.save_room_to_mongo(room)

    def list_all_areas_for(owner_id):
        areas = self.db().areas.find({ 'owner_id': owner_id },
            fields=['area_name'])
        return map(lambda a: dict(area_name=a['area_name'],
            area_id=str(a['_id'])), areas)

    def save_game(self, game):
        self._save_object(game, self.db().games)

    def load_game(self, game_id):
        return self._load_object(game_id, self.db().games)

    def get_or_create_player(self, player_id):
        player = self.db().players.find_one(username=player_id)
        if not player:
            player = Player(player_id)
            self._save_object(player, self.db().players)
        else:
            player = self._load_object(str(player['_id']), self.db().players)
        return player

    def save_player(self, player):
        self._save_object(player, self.db().players)
