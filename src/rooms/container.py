
import simplejson

from rooms.actor import Actor
from rooms.actor import State
from rooms.path_vector import Path
from rooms.player_actor import PlayerActor
from rooms.npc_actor import NpcActor
from rooms.item_actor import ItemActor
from rooms.room import Room
from rooms.room_container import RoomContainer
from rooms.room import RoomObject
from rooms.area import Area
from rooms.door import Door
from rooms.inventory import Inventory
from rooms.inventory import Item
from rooms.player import Player
from rooms.game import Game


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
        state = serialize_state(obj.state),
        log = obj.log,
        model_type = obj.model_type,
        script_class = obj.script.script_name if obj.script else None
    )

def _deserialize_actor(actor, data):
    actor.actor_id = data['actor_id']
    actor.path = data['path']
    actor.room_id = data['room_id']
    actor.state = create_state(data['state'])
    actor.log = data['log']
    actor.model_type = data['model_type']
    if data['script_class']:
        actor.load_script(data['script_class'])

def create_actor(data):
    actor = Actor(data['actor_id'])
    _deserialize_actor(actor, data)
    return actor


# State
def serialize_state(obj):
    return obj.copy()

def create_state(data):
    state = State()
    for key, value in data.items():
        state[key] = value
    return state

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
    return data

def create_npc_actor(data):
    npc_actor = NpcActor(data['actor_id'])
    _deserialize_actor(npc_actor, data)
    return npc_actor

# itemActor
def serialize_item_actor(obj):
    data = serialize_actor(obj)
    data['item_type'] = obj.item_type
    return data

def create_item_actor(data):
    item_actor = ItemActor(data['actor_id'], data['item_type'])
    _deserialize_actor(item_actor, data)
    return item_actor

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
        game_script_class = obj.game_script.script_name if obj.game_script else None,
        player_script_class = obj.player_script,
    )

def create_area(data):
    area = Area()
    area.area_name = data['area_name']
    area._room_map = data['room_map']
    area.owner_id = data['owner_id']
    area.entry_point_room_id = data['entry_point_room_id']
    area.entry_point_door_id = data['entry_point_door_id']
    # Second pass for top-level objects
    if data['game_script_class']:
        area.load_script(data['game_script_class'])
    area.player_script = data['player_script_class']
    return area

# Door
def serialize_door(obj):
    data = serialize_actor(obj)
    data.update(dict(
        exit_room_id=obj.exit_room_id,
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

# Player
def serialize_player(obj):
    data = dict(
        username = obj.username,
        game_id = obj.game_id,
        instance_id = obj.instance_id,
        actor_id = obj.actor_id,
    )
    return data

def create_player(data):
    player = Player(data['username'])
    player.game_id = data['game_id'],
    player.instance_id = data['instance_id'],
    player.actor_id = data['actor_id'],
    return player

# Game
def serialize_game(obj):
    data = dict(
        area_map = obj.area_map,
        owner_id = obj.owner_id,
        start_area_name = obj.start_area_name,
        open_game = obj.open_game,
    )
    return data

def create_game(data):
    game = Game()
    game.area_map = data['area_map']
    game.owner_id = data['owner_id']
    game.start_area_name = data['start_area_name']
    game.open_game = data['open_game']
    return game

object_serializers = dict(
    Actor=serialize_actor,
    PlayerActor=serialize_player_actor,
    PlayerKnowledge=serialize_player_knowledge,
    NpcActor=serialize_npc_actor,
    ItemActor=serialize_item_actor,
    Room=serialize_room,
    RoomObject=serialize_roomobject,
    Area=serialize_area,
    Door=serialize_door,
    Inventory=serialize_inventory,
    Path=serialize_path,
    State=serialize_state,
    Player=serialize_player,
    Game=serialize_game,
)

object_factories = dict(
    Actor=create_actor,
    PlayerActor=create_player_actor,
    PlayerKnowledge=create_player_knowledge,
    NpcActor=create_npc_actor,
    ItemActor=create_item_actor,
    Room=create_room,
    RoomObject=create_roomobject,
    Area=create_area,
    Door=create_door,
    Inventory=create_inventory,
    Path=create_path,
    State=create_state,
    Player=create_player,
    Game=create_game,
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


