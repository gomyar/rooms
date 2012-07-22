
import simplejson

from pymongo import Connection
from pymongo.helpers import bson

from actor import Actor
from path_vector import Path
from player_actor import PlayerActor
from npc_actor import NpcActor
from room import Room
from room_container import RoomContainer
from room import RoomObject
from area import Area
from door import Door
from inventory import Inventory
from inventory import Item
from scriptutils import load_script


class MongoRoomContainer(RoomContainer):
    def load_room(self, room_id):
        return load_room_from_mongo(room_id)

    def save_room(self, room_id, room):
        return save_room_to_mongo(room)


def save_room_to_mongo(room):
    encoded_str = simplejson.dumps(room, default=_encode, indent="    ")
    encoded_dict = simplejson.loads(encoded_str)
    if hasattr(room, "_id"):
        encoded_dict['_id'] = room._id
    rooms_db = _mongo_connection.rooms_db
    room_id = rooms_db.rooms.save(encoded_dict)
    room._id = room_id
    return str(room_id)

def load_room_from_mongo(room_id):
    rooms_db = _mongo_connection.rooms_db
    room_dict = rooms_db.rooms.find_one(bson.ObjectId(room_id))
    db_id = room_dict.pop('_id')
    room_str = simplejson.dumps(room_dict)
    room = simplejson.loads(room_str, object_hook=_decode)
    room._id = db_id
    return room


# Room
def serialize_room(obj):
    return dict(
        room_id = obj.room_id,
        position = obj.position,
        width = obj.width,
        height = obj.height,
        map_objects = obj.map_objects,
        actors = obj.actors,
        description = obj.description,
    )

def create_room(data):
    room = Room()
    room.room_id = data['room_id']
    room.position = data['position']
    room.width = data['width']
    room.height = data['height']
    room.map_objects = data['map_objects']
    room.actors = data['actors']
    room.description = data['description']
    for actor in room.actors.values():
        actor.room = room
    return room


# Actor
def serialize_actor(obj):
    return dict(
        actor_id = obj.actor_id,
        path = obj.path,
        room_id = obj.room.room_id,
        state = obj.state,
        log = obj.log,
    )

def _deserialize_actor(actor, data):
    actor.actor_id = data['actor_id']
    actor.path = data['path']
    actor.room_id = data['room_id']
    actor.state = data['state']
    actor.log = data['log']

def create_actor(data):
    actor = Actor(data['actor_id'])
    _deserialize_actor(actor, data)
    return actor


# Path
def serialize_path(obj):
    return dict(
        path=obj.path,
        speed=obj.speed,
    )

def create_path(data):
    path = Path()
    path.path = data['path']
    path.speed = data['speed']
    return path

# PlayerActor
def serialize_player_actor(obj):
    data = serialize_actor(obj)
    data['inventory'] = obj.inventory
    data['data'] = obj.data
    return data

def create_player_actor(data):
    player_actor = PlayerActor(data['actor_id'])
    player_actor.inventory = data['inventory']
    player_actor.data = data['data']
    _deserialize_actor(player_actor, data)
    return player_actor

# NPCActor
def serialize_npc_actor(obj):
    data = serialize_actor(obj)
    data['npc_script_class'] = obj.npc_script.__class__.__name__
    return data

def create_npc_actor(data):
    npc_actor = NpcActor(data['actor_id'])
    _deserialize_actor(npc_actor, data)
    npc_actor.load_script(data['npc_script_class'])
    return npc_actor

# RoomObject
def serialize_roomobject(obj):
    return dict(
        width=obj.width,
        height=obj.height,
        position=obj.position,
        object_type=obj.object_type,
        facing=obj.facing,
    )

def create_roomobject(data):
    room_object = RoomObject(data['object_type'], data['width'],
        data['height'], data['position'], data['facing'])
    return room_object

# Area
def serialize_area(obj):
    return dict(
        area_name = obj.area_name,
        owner_id = obj.owner_id,
        room_map = obj.rooms._room_map,
        entry_point_room_id = obj.entry_point_room_id,
        entry_point_door_id = obj.entry_point_door_id,
        game_script_class = obj.game_script.__class__.__name__
    )

def create_area(data):
    area = Area()
    area.area_name = data['area_name']
    area.rooms = MongoRoomContainer(area)
    area.rooms._room_map = data['room_map']
    area.owner_id = data['owner_id']
    area.entry_point_room_id = data['entry_point_room_id']
    area.entry_point_door_id = data['entry_point_door_id']
    # Second pass for top-level objects
    area.game_script = load_script(data['game_script_class'])
    return area

# Door
def serialize_door(obj):
    data = serialize_actor(obj)
    data.update(dict(
        exit_room_id=obj.exit_room.room_id,
        exit_door_id=obj.exit_door_id,
        position=(obj.x(), obj.y()),
        opens_direction=obj.opens_direction,
    ))
    return data

def create_door(data):
    door = Door()
    _deserialize_actor(door, data)
    door.exit_room_id = data['exit_room_id']
    door.exit_door_id = data['exit_door_id']
    door.set_position(data['position'])
    door.opens_direction = data['opens_direction']
    return door

# Inventory
def serialize_inventory(obj):
    data = dict(
        items=obj._items)
    return data

def create_inventory(data):
    inv = Inventory()
    inv._items = data['items']
    return inv

# Inventory item
def serialize_inventory_item(obj):
    return obj.copy()

def create_inventory_item(data):
    item = Item()
    for key, value in data:
        items[key] = value
    return item

# Player Knownledge
def serialize_player_knowledge(obj):
    return obj.copy()

def create_player_knowledge(data):
    item = Item()
    for key, value in data:
        items[key] = value
    return item

object_serializers = dict(
    Actor=serialize_actor,
    PlayerActor=serialize_player_actor,
    PlayerKnowledge=serialize_player_knowledge,
    NpcActor=serialize_npc_actor,
    Room=serialize_room,
    RoomObject=serialize_roomobject,
    Area=serialize_area,
    Door=serialize_door,
    Inventory=serialize_inventory,
    Path=serialize_path,
)

object_factories = dict(
    Actor=create_actor,
    PlayerActor=create_player_actor,
    PlayerKnowledge=create_player_knowledge,
    NpcActor=create_npc_actor,
    Room=create_room,
    RoomObject=create_roomobject,
    Area=create_area,
    Door=create_door,
    Inventory=create_inventory,
    Path=create_path,
)

def _encode(obj):
    obj_name =  type(obj).__name__
    if obj_name in object_serializers:
        data = object_serializers[obj_name](obj)
        data['__type__'] = obj_name
        return data
    raise TypeError("Cannot serialize object %s" % obj_name)


def _decode(data):
    if "__type__" in data:
        obj_type = data.pop('__type__')
        if obj_type in object_factories:
            return object_factories[obj_type](data)
        else:
            raise TypeError("No such type:%s" % obj_type)
    return data


def deserialize_area(data):
    return simplejson.loads(data, object_hook=_decode)

def serialize_area(area):
    return simplejson.dumps(area, default=_encode, indent="    ")

def init_mongo(host='localhost', port=27017):
    global _mongo_connection
    _mongo_connection = Connection(host, port)

def load_area(area_id):
    rooms_db = _mongo_connection.rooms_db
    area_dict = rooms_db.areas.find_one(bson.ObjectId(area_id))
    area_dict.pop('_id')
    area_str = simplejson.dumps(area_dict)
    area = simplejson.loads(area_str, object_hook=_decode)
    return area

def save_area(area):
    encoded_str = simplejson.dumps(area, default=_encode, indent="    ")
    encoded_dict = simplejson.loads(encoded_str)
    rooms_db = _mongo_connection.rooms_db
    rooms_db.areas.save(encoded_dict)
    for room_id, room in area.rooms._rooms.items():
        print "Saved room %s:%s" % (room_id, room._id)
        save_room_to_mongo(room)

def list_all_areas_for(owner_id):
    rooms_db = _mongo_connection.rooms_db
    areas = rooms_db.areas.find({ 'owner_id': owner_id }, fields=['area_name'])
    return map(lambda a: dict(area_name=a['area_name'], area_id=str(a['_id'])),
        areas)
