
import simplejson

from pymongo import Connection
from pymongo.helpers import bson

from actor import Actor
from player_actor import PlayerActor
from npc_actor import NpcActor
from room import Room
from room import RoomObject
from area import Area
from door import Door
from scriptutils import load_script

# Actor
def serialize_actor(obj):
    return dict(
        actor_id = obj.actor_id,
        path = obj.path,
        speed = obj.speed,
        room_id = obj.room.room_id,
        state = obj.state,
        log = obj.log,
    )

def _deserialize_actor(actor, data):
    actor.actor_id = data['actor_id']
    actor.path = data['path']
    actor.speed = data['speed']
    actor.room_id = data['room_id']
    actor.state = data['state']
    actor.log = data['log']

def create_actor(data):
    actor = Actor(data['actor_id'])
    _deserialize_actor(actor, data)
    return actor

# PlayerActor
def serialize_player_actor(obj):
    return serialize_actor(obj)

def create_player_actor(data):
    player_actor = PlayerActor(data['actor_id'])
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

# Room
def serialize_room(obj):
    return dict(
        room_id = obj.room_id,
        position = obj.position,
        width = obj.width,
        height = obj.height,
        map_objects = obj.map_objects,
        actor_ids = [actor_id for actor_id, _ in obj.actors.items()],
        description = obj.description,
    )

def create_room(data):
    room = Room()
    room.room_id = data['room_id']
    room.position = data['position']
    room.width = data['width']
    room.height = data['height']
    room.map_objects = data['map_objects']
    room._actor_ids = data['actor_ids']
    room.description = data['description']
    return room

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
        actors = obj.actors,
        rooms = obj.rooms,
        owner_id = obj.owner_id,
        entry_point_room_id = obj.entry_point_room_id,
        entry_point_door_id = obj.entry_point_door_id,
        game_script_class = obj.game_script.__class__.__name__
    )

def create_area(data):
    area = Area()
    area.area_name = data['area_name']
    area.actors = dict(data['actors'])
    area.rooms = dict(data['rooms'])
    area.owner_id = data['owner_id']
    area.entry_point_room_id = data['entry_point_room_id']
    area.entry_point_door_id = data['entry_point_door_id']
    # Second pass for top-level objects
    if area.rooms:
        for room in area.rooms.values():
            room.actors = dict([(actor_id, area.actors[actor_id]) for \
                actor_id in room._actor_ids])
            for actor in room.actors.values():
                actor.room = room
        # hook up doors
        for room in area.rooms.values():
            for door in room.all_doors():
                door.exit_room = area.rooms[door.exit_room_id]
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


object_serializers = dict(
    Actor=serialize_actor,
    PlayerActor=serialize_player_actor,
    NpcActor=serialize_npc_actor,
    Room=serialize_room,
    RoomObject=serialize_roomobject,
    Area=serialize_area,
    Door=serialize_door,
)

object_factories = dict(
    Actor=create_actor,
    PlayerActor=create_player_actor,
    NpcActor=create_npc_actor,
    Room=create_room,
    RoomObject=create_roomobject,
    Area=create_area,
    Door=create_door,
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

def load_base_area(area_id):
    rooms_db = _mongo_connection.rooms_db
    return _decode(rooms_db.base_areas.find_one(bson.ObjectId(area_id)))

def save_base_area(area):
    encoded = _encode(area)
    rooms_db = _mongo_connection.rooms_db
    rooms_db.base_areas.save(encoded)

def list_all_areas_for(owner_id):
    rooms_db = _mongo_connection.rooms_db
    areas = rooms_db.areas.find({ 'owner_id': owner_id }, fields=['area_name'])
    return map(lambda a: dict(area_name=a['area_name'], area_id=str(a['_id'])),
        areas)
