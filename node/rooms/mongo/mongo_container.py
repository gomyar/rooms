
import simplejson

from pymongo import Connection
from pymongo.helpers import bson

from rooms.room_container import RoomContainer

from rooms.container import _decode
from rooms.container import _encode


class MongoRoomContainer(RoomContainer):
    def __init__(self, area, mongo_container):
        super(MongoRoomContainer, self).__init__(area)
        self.mongo_container = mongo_container

    def load_room(self, room_id):
        return self.load_room_from_mongo(room_id)

    def save_room(self, room_id, room):
        return self.save_room_to_mongo(room)

    def save_room_to_mongo(self, room):
        encoded_str = simplejson.dumps(room, default=_encode, indent="    ")
        encoded_dict = simplejson.loads(encoded_str)
        if hasattr(room, "_id"):
            encoded_dict['_id'] = room._id
        rooms_db = self.mongo_container._mongo_connection.rooms_db
        room_id = rooms_db.rooms.save(encoded_dict)
        room._id = room_id
        return str(room_id)

    def load_room_from_mongo(self, room_id):
        rooms_db = self.mongo_container._mongo_connection.rooms_db
        room_dict = rooms_db.rooms.find_one(bson.ObjectId(room_id))
        db_id = room_dict.pop('_id')
        room_str = simplejson.dumps(room_dict)
        room = simplejson.loads(room_str, object_hook=_decode)
        room._id = db_id
        return room


class MongoContainer(object):
    def __init__(self, host='localhost', port=27017):
        self.host = host
        self.port = port
        self._mongo_connection = None

    def init_mongo(self):
        self._mongo_connection = Connection(self.host, self.port)

    def load_area(self, area_id):
        rooms_db = self._mongo_connection.rooms_db
        area_dict = rooms_db.areas.find_one(bson.ObjectId(area_id))
        area_dict.pop('_id')
        area_str = simplejson.dumps(area_dict)
        area = simplejson.loads(area_str, object_hook=_decode)
        area.rooms = MongoRoomContainer(area, self)
        area.rooms._room_map = area._room_map
        return area

    def save_area(self, area):
        encoded_str = simplejson.dumps(area, default=_encode, indent="    ")
        encoded_dict = simplejson.loads(encoded_str)
        rooms_db = self._mongo_connection.rooms_db
        rooms_db.areas.save(encoded_dict)
        for room in area.rooms._rooms.values():
            self.save_room_to_mongo(room)

    def list_all_areas_for(owner_id):
        rooms_db = self._mongo_connection.rooms_db
        areas = rooms_db.areas.find({ 'owner_id': owner_id },
            fields=['area_name'])
        return map(lambda a: dict(area_name=a['area_name'],
            area_id=str(a['_id'])), areas)
