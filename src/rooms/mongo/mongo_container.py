
import simplejson

from pymongo import Connection
from pymongo.helpers import bson

from rooms.room_container import RoomContainer

from rooms.container import Container
from rooms.player import Player

import logging
log = logging.getLogger("rooms.mongocontainer")


class MongoRoomContainer(RoomContainer):
    def __init__(self, area, mongo_container):
        super(MongoRoomContainer, self).__init__(area)
        self.mongo_container = mongo_container

    def load_room(self, room_id):
        return self.mongo_container.load_room(room_id)

    def save_room(self, room_id, room):
        return self.mongo_container.save_room(room)


class MongoContainer(object):
    def __init__(self, host='localhost', port=27017, dbname="rooms_db"):
        self.host = host
        self.port = port
        self.dbname = dbname
        self._mongo_connection = None
        self.container = None

    def db(self):
        return getattr(self._mongo_connection, self.dbname)

    def _collection(self, name):
        return getattr(self.db(), name)

    def load_object(self, object_id, dbase_name):
        obj_dict = self._collection(dbase_name).find_one(
            bson.ObjectId(object_id))
        obj_dict['_id'] = str(obj_dict['_id'])
        return obj_dict

    def save_object(self, encoded_dict, dbase_name, object_id):
        encoded_dict['_id'] = object_id
        obj_id = collection.save(encoded_dict)
        return str(obj_id)

    def object_exists(self, dbase_name, search_fields):
        return self._collection(dbase_name).find_one(search_fields)

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
