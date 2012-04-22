
import simplejson

from actor import Actor
from player_actor import PlayerActor
from room import Room
from area import Area

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

# Room
def serialize_room(obj):
    return dict(
        room_id = obj.room_id,
        x = obj.x,
        y = obj.y,
        width = obj.width,
        height = obj.height,
        map_objects = obj.map_objects,
        actor_ids = [actor_id for actor_id, _ in obj.actors.items()]
    )

def create_room(data):
    room = Room()
    room.room_id = data['room_id']
    room.x = data['x']
    room.y = data['y']
    room.width = data['width']
    room.height = data['height']
    room.map_objects = data['map_objects']
    room._actor_ids = data['actor_ids']
    return room

# Area
def serialize_area(obj):
    return dict(
        actors = obj.actors,
        rooms = obj.rooms,
    )

def create_area(data):
    area = Area()
    area.actors = data['actors']
    area.rooms = data['rooms']
    # Second pass for top-level objects
    for room in area.rooms.values():
        room.actors = dict([(actor_id, area.actors[actor_id]) for actor_id in \
            room._actor_ids])
        for actor in room.actors.values():
            actor.room = room
        del room._actor_ids
    for actor in area.actors.values():
        del actor.room_id
    return area


object_serializers = dict(
    Actor=serialize_actor,
    PlayerActor=serialize_player_actor,
    Room=serialize_room,
    Area=serialize_area,
)

object_factories = dict(
    Actor=create_actor,
    Room=create_room,
    Area=create_area,
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

def load_area(filename):
    return _decode(open(filename).read())

def save_area(area, filename):
    encoded = _encode(area)
    out = open(filename, "w")
    out.write(encoded)
    out.close()
