
import simplejson

from pymongo import Connection
from pymongo.helpers import bson

from rooms.container import Container
from rooms.player import Player

import logging
log = logging.getLogger("rooms.mongocontainer")


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

    def save_object(self, encoded_dict, dbase_name, object_id=None):
        if object_id:
            encoded_dict['_id'] = bson.ObjectId(object_id)
        return self._collection(dbase_name).save(encoded_dict)

    def object_exists(self, dbase_name, **search_fields):
        return bool(self.filter_one(dbase_name, **search_fields))

    def filter_one(self, dbase_name, **search_fields):
        return self._collection(dbase_name).find_one(search_fields)

    def filter(self, dbase_name, **search_fields):
        return self._collection(dbase_name).find(search_fields)

    def _save_object(self, obj, collection):
        encoded_str = simplejson.dumps(obj, default=self.container._encode,
            indent="    ")
        encoded_dict = simplejson.loads(encoded_str)
        if hasattr(obj, "_id"):
            encoded_dict['_id'] = bson.ObjectId(obj._id)
        obj_id = collection.save(encoded_dict)
        obj._id = str(obj_id)
        return obj._id

    def _load_object(self, obj_id, collection):
        obj_dict = collection.find_one(bson.ObjectId(obj_id))
        db_id = obj_dict.pop('_id')
        obj_str = simplejson.dumps(obj_dict)
        obj = simplejson.loads(obj_str, object_hook=self.container._decode)
        obj._id = db_id
        return obj

    def init_mongo(self):
        self._mongo_connection = Connection(self.host, self.port)
