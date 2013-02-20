
import simplejson

from rooms.actor import Actor
from rooms.actor import State
from rooms.waypoint import Path
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
from rooms.circles import Circles
from rooms.item_registry import ItemRegistry
from rooms.null import Null


class Container(object):
    def __init__(self, dbase, geography, save_manager=None):
        self.dbase = dbase
        self.geography = geography
        self.save_manager = save_manager or Null()

        self.object_serializers = dict(
            Actor=self._serialize_actor,
            PlayerActor=self._serialize_player_actor,
            PlayerKnowledge=self._serialize_player_knowledge,
            NpcActor=self._serialize_npc_actor,
            ItemActor=self._serialize_item_actor,
            Room=self._serialize_room,
            RoomObject=self._serialize_roomobject,
            Area=self._serialize_area,
            Door=self._serialize_door,
            Inventory=self._serialize_inventory,
            Path=self._serialize_path,
            State=self._serialize_state,
            Player=self._serialize_player,
            Game=self._serialize_game,
            Circles=self._serialize_circles,
            ItemRegistry=self._serialize_item_registry,
            Item=self._serialize_item,
        )

        self.object_factories = dict(
            Actor=self._create_actor,
            PlayerActor=self._create_player_actor,
            PlayerKnowledge=self._create_player_knowledge,
            NpcActor=self._create_npc_actor,
            ItemActor=self._create_item_actor,
            Room=self._create_room,
            RoomObject=self._create_roomobject,
            Area=self._create_area,
            Door=self._create_door,
            Inventory=self._create_inventory,
            Path=self._create_path,
#            State=self._create_state,
            Player=self._create_player,
            Game=self._create_game,
            Circles=self._create_circles,
            ItemRegistry=self._create_item_registry,
            Item=self._create_item,
        )

    def load_game(self, game_id):
        return self._load_object(game_id, "games")

    def save_game(self, game):
        return self._save_object(game, "games")

    def _load_filter(self, collection, **fields):
        enc_dict = self.dbase.filter_one(collection, **fields)
        if enc_dict:
            db_id = enc_dict.pop('_id')
            obj = self._dict_to_obj(enc_dict)
            obj._id = str(db_id)
            return obj
        else:
            return None

    def load_area(self, area_id):
        area = self._load_filter("areas", area_id=area_id)
        area.rooms = RoomContainer(area, self)
        area.rooms._room_map = area._room_map
        return area

    def save_area(self, area):
        return self._save_object(area, "areas")

    def load_room(self, room_id):
        return self._load_object(room_id, "rooms")

    def save_room(self, room):
        _id = self._save_object(room, "rooms")
        for player_actor in room.player_actors():
            self.save_player(player_actor.player)
        return _id

    def save_player(self, player):
        return self._save_object(player, "players")

    def load_player(self, username):
        return self._load_filter("players", username=username)

    def get_or_create_player(self, username):
        if self.dbase.object_exists("players", username=username):
            return self.load_player(username)
        else:
            player = Player(username)
            self.save_player(player)
            return player

    def update_actor(self, actor):
        actor_dict = self._obj_to_dict(actor)

        if isinstance(actor, PlayerActor):
            self.save_player(actor.player)

        self.dbase.update_object(actor.room, "rooms", "actors.%s" % (
            actor.actor_id,), actor_dict)

    def remove_actor(self, room, actor):
        self.dbase.remove_object(room, "rooms", "actors.%s" % (
            actor.actor_id,))

    def _save_object(self, saved_object, dbase_name):
        if getattr(saved_object, '_id', None):
            db_id = saved_object._id
            saved_object._id = None
        else:
            db_id = None
        object_dict = self._obj_to_dict(saved_object)
        db_id = self.dbase.save_object(object_dict, dbase_name, db_id)
        saved_object._id = str(db_id)
        return str(db_id)

    def _load_object(self, object_id, dbase_name):
        enc_dict = self.dbase.load_object(object_id, dbase_name)
        if enc_dict:
            db_id = enc_dict.pop('_id')
            obj = self._dict_to_obj(enc_dict)
            obj._id = str(db_id)
            return obj
        else:
            return None

    def _obj_to_dict(self, pyobject):
        encoded_str = simplejson.dumps(pyobject, default=self._encode,
            indent="    ")
        return simplejson.loads(encoded_str)

    def _dict_to_obj(self, obj_dict):
        obj_str = simplejson.dumps(obj_dict)
        return simplejson.loads(obj_str, object_hook=self._decode)

    # Room
    def _serialize_room(self, obj):
        return dict(
            room_id = obj.room_id,
            position = obj.position,
            width = obj.width,
            height = obj.height,
            map_objects = obj.map_objects,
            actors = obj.actors,
            description = obj.description,
        )

    def _create_room(self, data):
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
            if actor._docked_with_id:
                room.actors[actor._docked_with_id].dock(actor)
        room.geog = self.geography
        room.save_manager = self.save_manager
        return room


    # Actor
    def _serialize_actor(self, obj):
        return dict(
            actor_id = obj.actor_id,
            name = obj.name,
            actor_type = obj.actor_type,
            path = obj.path,
            speed = obj.speed,
            room_id = obj.room.room_id,
            state = self._serialize_state(obj.state),
            log = obj.log,
            model_type = obj.model_type,
            inventory = obj.inventory,
            script_class = obj.script.script_name if obj.script else None,
            circles = obj.circles,
            health = obj._health,
            visible = obj.visible,
            _docked_with_id = obj.docked_with.actor_id if obj.docked_with else None,
        )

    def _deserialize_actor(self, actor, data):
        actor.actor_id = data['actor_id']
        actor.name = data['name']
        actor.actor_type = data['actor_type']
        actor.path = data['path']
        actor.speed = data['speed']
        actor.room_id = data['room_id']
        actor.state = self._create_state(data['state'], actor)
        actor.log = data['log']
        actor.model_type = data['model_type']
        actor.inventory = data['inventory']
        if data['script_class']:
            actor.load_script(data['script_class'])
        actor.circles = data['circles']
        actor._health = data['health']
        actor.visible = data['visible']
        actor._docked_with_id = data['_docked_with_id']
        actor.save_manager = self.save_manager

    def _create_actor(self, data):
        actor = Actor(data['actor_id'])
        self._deserialize_actor(actor, data)
        return actor

    # Circles
    def _serialize_circles(self, obj):
        return dict(circle_id=obj.circle_id, circles=obj.circles)

    def _create_circles(self, data):
        circle = Circles()
        circle.circle_id = data['circle_id']
        circle.circles = data['circles']
        return circle

    # State
    def _serialize_state(self, obj):
        return obj.copy()

    def _create_state(self, data, actor):
        state = State(actor)
        for key, value in data.items():
            state[key] = value
        return state

    # Path
    def _serialize_path(self, obj):
        return dict(
            path=obj.path,
        )

    def _create_path(self, data):
        path = Path()
        path.path = data['path']
        return path

    # PlayerActor
    def _serialize_player_actor(self, obj):
        data = self._serialize_actor(obj)
        data['_player_id'] = obj.player.username
        return data

    def _create_player_actor(self, data):
        player = self.load_player(data['_player_id'])
        player_actor = PlayerActor(player, actor_id=data['actor_id'])
        self._deserialize_actor(player_actor, data)
        return player_actor

    # NPCActor
    def _serialize_npc_actor(self, obj):
        data = self._serialize_actor(obj)
        return data

    def _create_npc_actor(self, data):
        npc_actor = NpcActor(data['actor_id'])
        self._deserialize_actor(npc_actor, data)
        return npc_actor

    # itemActor
    def _serialize_item_actor(self, obj):
        data = self._serialize_actor(obj)
        data['item_type'] = obj.item_type
        return data

    def _create_item_actor(self, data):
        item_actor = ItemActor(data['actor_id'], data['item_type'])
        self._deserialize_actor(item_actor, data)
        return item_actor

    # RoomObject
    def _serialize_roomobject(self, obj):
        return dict(
            width=obj.width,
            height=obj.height,
            position=obj.position,
            object_type=obj.object_type,
            facing=obj.facing,
        )

    def _create_roomobject(self, data):
        room_object = RoomObject(data['object_type'], data['width'],
            data['height'], data['position'], data['facing'])
        return room_object

    # Area
    def _serialize_area(self, obj):
        return dict(
            area_id = obj.area_id,
            owner_id = obj.owner_id,
            room_map = obj.rooms._room_map,
            entry_point_door_id = obj.entry_point_door_id,
        )

    def _create_area(self, data):
        area = Area()
        area.area_id = data['area_id']
        area._room_map = data['room_map']
        area.owner_id = data['owner_id']
        area.entry_point_door_id = data['entry_point_door_id']
        return area

    # Door
    def _serialize_door(self, obj):
        data = self._serialize_actor(obj)
        data.update(dict(
            exit_room_id=obj.exit_room_id,
            exit_door_id=obj.exit_door_id,
            exit_room_description=obj.exit_room_description,
            position=(obj.x(), obj.y()),
            opens_direction=obj.opens_direction,
        ))
        return data

    def _create_door(self, data):
        door = Door()
        self._deserialize_actor(door, data)
        door.exit_room_id = data['exit_room_id']
        door.exit_door_id = data['exit_door_id']
        door.exit_room_description = data['exit_room_description']
        door.set_position(data['position'])
        door.opens_direction = data['opens_direction']
        return door

    # Inventory
    def _serialize_inventory(self, obj):
        data = dict(
            items=obj._items)
        return data

    def _create_inventory(self, data):
        inv = Inventory()
        inv._items = data['items']
        return inv

    # Inventory item
    def _serialize_inventory_item(self, obj):
        return obj.copy()

    def _create_inventory_item(self, data):
        item = Item()
        for key, value in data:
            items[key] = value
        return item

    # Player Knownledge
    def _serialize_player_knowledge(self, obj):
        return obj.copy()

    def _create_player_knowledge(self, data):
        item = Item()
        for key, value in data:
            items[key] = value
        return item

    # Item Registry
    def _serialize_item_registry(self, obj):
        return obj._items

    def _create_item_registry(self, data):
        registry = ItemRegistry()
        registry._items = dict([(key, self._create_item(value)) for \
            (key, value) in data.items()])
        return registry

    # Item from Registry
    def _serialize_item(self, obj):
        item = dict(item_type=obj.item_type)
        item.update(obj.copy())
        return item

    def _create_item(self, data):
        item = Item(item_type=data['item_type'])
        item.update(data)
        return item

    # Player
    def _serialize_player(self, obj):
        data = dict(
            username = obj.username,
            game_id = obj.game_id,
            area_id = obj.area_id,
            actor_id = obj.actor_id,
            room_id = obj.room_id,
            state = obj.state,
        )
        return data

    def _create_player(self, data):
        player = Player(data['username'])
        player.game_id = data['game_id']
        player.area_id = data['area_id']
        player.actor_id = data['actor_id']
        player.room_id = data['room_id']
        player.state = data['state']
        return player

    # Game
    def _serialize_game(self, obj):
        data = dict(
            owner_id = obj.owner_id,
            start_areas = obj.start_areas,
            open_game = obj.open_game,
            item_registry = obj.item_registry,
            player_script_class = obj.player_script,
        )
        return data

    def _create_game(self, data):
        game = Game()
        game.owner_id = data['owner_id']
        game.start_areas = data['start_areas']
        game.open_game = data['open_game']
        game.item_registry = data['item_registry']
        game.player_script = data['player_script_class']
        return game


    def _encode(self, obj):
        obj_name =  type(obj).__name__
        if obj_name in self.object_serializers:
            data = self.object_serializers[obj_name](obj)
            data['__type__'] = obj_name
            return data
        raise TypeError("Cannot serialize object %s" % obj_name)


    def _decode(self, data):
        if "__type__" in data:
            obj_type = data.pop('__type__')
            if obj_type in self.object_factories:
                return self.object_factories[obj_type](data)
            else:
                raise TypeError("No such type:%s" % obj_type)
        return data
