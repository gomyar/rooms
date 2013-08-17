
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
        if not obj_dict:
            raise Exception("Object %s not found in dbase %s" % (object_id,
                dbase_name))
        obj_dict['_id'] = str(obj_dict['_id'])
        return obj_dict

    def save_object(self, encoded_dict, dbase_name, object_id=None):
        if object_id:
            encoded_dict['_id'] = bson.ObjectId(object_id)
        return self._collection(dbase_name).save(encoded_dict)

    def remove(self, collection_name, **kwargs):
        self._collection(collection_name).remove(kwargs)

    def object_exists(self, dbase_name, **search_fields):
        return bool(self.filter_one(dbase_name, **search_fields))

    def filter_one(self, dbase_name, **search_fields):
        return self._collection(dbase_name).find_one(search_fields)

    def filter(self, dbase_name, **search_fields):
        return self._collection(dbase_name).find(search_fields)

    def _load_object(self, obj_id, collection):
        obj_dict = collection.find_one(bson.ObjectId(obj_id))
        db_id = obj_dict.pop('_id')
        obj_str = simplejson.dumps(obj_dict)
        obj = simplejson.loads(obj_str, object_hook=self.container._decode)
        obj._id = db_id
        return obj

    def update_object(self, obj, collection_name, update_key, update_obj):
        try:
            self._collection(collection_name).update(
                {'_id': bson.ObjectId(obj._id) },
                {
                    '$set': { update_key: update_obj },
                },
                upsert=True,
                )
        except:
            log.exception("Exception updating object in %s.update_key: %s",
                collection_name, update_obj)
            raise

    def update_object_fields(self, obj, collection_name, **kwargs):
        try:
            self._collection(collection_name).update(
                {'_id': bson.ObjectId(obj._id) },
                {
                    '$set': kwargs,
                },
                upsert=True,
                )
        except:
            log.exception("Exception updating object in %s.update_key: %s",
                collection_name, update_obj)
            raise

    def remove_object(self, obj, collection_name, remove_key):
        try:
            self._collection(collection_name).update(
                {'_id': obj._id },
                {
                    '$unset': { remove_key: 1 },
                },
                )
        except:
            log.exception("Exception removing object %s.%s.%s",
                collection_name, obj._id, remove_key)

    def init_mongo(self):
        self._mongo_connection = Connection(self.host, self.port)

    def drop_collection(self, collection_id):
        self.db().drop_collection(collection_id)

    def drop_database(self):
        ''' Careful now '''
        self._mongo_connection.drop_database(self.dbname)
