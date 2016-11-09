import json
from datetime import datetime
import gevent
import uuid
import time
from gevent.queue import Queue

from rooms.utils import IDFactory
from rooms.game import Game
from rooms.player import PlayerActor
from rooms.room import Room, Door
from rooms.position import Position
from rooms.actor import Actor
from rooms.script import Script
from rooms.vector import Vector
from rooms.state import SyncDict
from rooms.state import SyncList
from rooms.actor_loader import ActorLoader
from rooms.online_node import OnlineNode
from rooms.item_registry import ItemRegistry
from rooms.geography.basic_geography import BasicGeography
from rooms.room_builder import SimpleRoomBuilder
from rooms.timer import Timer

import logging
log = logging.getLogger("rooms.container")


class Container(object):
    def __init__(self, dbase, node):
        self.dbase = dbase
        self.geography = BasicGeography()
        self.node = node
        self.room_builder = SimpleRoomBuilder()
        self.item_registry = ItemRegistry()
        self.serializers = dict(
            Game=self._serialize_game,
            PlayerActor=self._serialize_player,
            Room=self._serialize_room,
            Door=self._serialize_door,
            Position=self._serialize_position,
            Actor=self._serialize_actor,
            Vector=self._serialize_vector,
            SyncDict=self._serialize_syncdict,
            SyncList=self._serialize_synclist,
            OnlineNode=self._serialize_onlinenode,
        )
        self.builders = dict(
            Game=self._build_game,
            PlayerActor=self._build_player,
            Room=self._build_room,
            Door=self._build_door,
            Position=self._build_position,
            Actor=self._build_actor,
            Vector=self._build_vector,
            SyncDict=self._build_syncdict,
            SyncList=self._build_synclist,
            OnlineNode=self._build_onlinenode,
        )
        self._remove_queue = Queue()
        self._remove_gthread = None

    def start_container(self):
        self._running = True
        self._remove_gthread = gevent.spawn(self._run_remove_queue)

    def stop_container(self):
        self._running = False
        log.info("Stopping container - waiting for remove queue")
        self._remove_queue.put(None)
        self._remove_gthread.join()
        log.info("Container stopped")

    def new_token(self):
        return str(uuid.uuid1())

    def create_player_token(self, game_id, username, timeout_seconds):
        enc_conn = self.dbase.find_and_modify(
            'actors',
            query={'game_id': game_id, '__type__': 'PlayerActor'},
            update={
                '$set':{
                    'timeout_time': Timer.now() + timeout_seconds,
                    'token': self.new_token()},
            },
            new=True,
            fields=['game_id', 'username', 'token', 'timeout_time', 'room_id',
                    'actor_id', 'node_name'],
        )
        return enc_conn

    def get_player_token(self, token):
        player = self.dbase.filter_one(
            'actors',
            query={'token': token,
                   'timeout_time': {'$gt': Timer.now()},
                   '__type__': 'PlayerActor'},
            fields=['game_id', 'username', 'token', 'timeout_time', 'room_id',
                    'actor_id', 'node_name'],
        )
        return player

    def get_or_create_player(self, game_id, username, room_id):
        return self.dbase.find_and_modify(
            'actors',
            query={'game_id': game_id, 'username': username,
                   '__type__': 'PlayerActor'},
            update={
                '$setOnInsert': self._new_player_data(game_id, room_id,
                                                      username, 'active'),
                '$set':{'token': self.new_token(),
                    'timeout_time': Timer.now() + 300,}
            },
            upsert=True,
            new=True,
        )

    def _new_player_data(self, game_id, room_id, username, status):
        return {
            'game_id': game_id,
            'username': username,
            'room_id':room_id,
            'status': status,
            'actor_type': 'player',
            'visible': True,
            'parent_id': None,
            'state': {"__type__" : "SyncDict"},
            'path': [],
            'speed': 1.0,
            'docked_with': None,
            'vector': {
                "__type__" : "Vector",
                "start_time": time.time(),
                "start_pos": {"x": 0, "y": 0, "z": 0, "__type__": "Position"},
                "end_time": time.time(),
                "end_pos": {"x": 0, "y": 0, "z": 0, "__type__": "Position"},
            },
            'actor_id': IDFactory.create_id(),
            '__type__': 'PlayerActor',
            '_loadstate': 'limbo',
            'script_name': 'player_script',
        }

    def load_room(self, game_id, room_id):
        room = self._load_filter_one("rooms", dict(game_id=game_id, room_id=room_id))
        room.item_registry = self.item_registry
        self.load_actors_for_room(room)
        return room

    def load_actors_for_room(self, room):
        game_id = room.game_id
        room_id = room.room_id
        log.debug("Load actors for room: %s %s", game_id, room_id)
        actors_list = self._load_filter("actors", dict(game_id=game_id,
            room_id=room_id, docked_with=None))
        log.debug("Found %s actors", len(actors_list))
        for actor in actors_list:
            docked_actors = ActorLoader(room)._load_docked(game_id, actor)
            log.debug("Loaded docked actors: %s", docked_actors)
            room.put_actor(actor)
            for docked in docked_actors:
                room.put_actor(docked)

    def save_room(self, room):
        self._save_object(room, "rooms", active=False, requested=False)

    def save_actors(self, actors):
        for actor in actors:
            self.save_actor(actor)

    def create_room_with_actors(self, game_id, room_id):
        if self.room_exists(game_id, room_id):
            raise Exception("Room %s %s already exists" % (game_id, room_id))
        room = self.create_room(game_id, room_id)
        self.load_actors_for_room(room)
        return room

    # deprecated
    def create_room(self, game_id, room_id):
        room = self.room_builder.create(game_id, room_id)
        room.geography = self.geography
        room.item_registry = self.item_registry
        self.save_room(room)
        return room

    def request_create_room(self, game_id, room_id):
        # push into dbase
        return self.dbase.find_and_modify(
            'rooms',
            query={'game_id': game_id, '__type__': 'Room'},
            update={
                '$set':{'requested':True},
                '$setOnInsert':{'active': False,'node_name': None,
                    '__type__': 'Room', 'state': {}, 'game_id': game_id,
                    'room_id': room_id},
            },
            upsert=True,
            new=True,
        )

    def load_next_pending_room(self, node_name):
        room_data = self.dbase.find_and_modify(
            'rooms',
            query={'active': False, 'requested': True, '__type__': 'Room', 'node_name': None},
            update={
                '$set':{'active': True, 'requested': False, 'node_name': node_name},
                '$setOnInsert':{'active': False, 'initialized': False},
            },
            new=True,
        )
        if room_data:
            return self._decode_enc_dict(room_data)
        else:
            return None

    def disassociate_rooms(self, node_name):
        self.dbase.update_many_fields(
            'rooms', {'__type__': 'Room', 'node_name': node_name},
            {'node_name': None, 'active': False, 'requested': False})

    def create_actor(self, room, actor_type, script, username=None,
            state=None, visible=True, parent_id=None, position=None):
        actor = Actor(room, actor_type, script, username, visible=visible,
            game_id=room.game_id)
        actor.state.update(state or {})
        actor.parent_id = parent_id
        if position:
            actor._set_position(position)
        self.save_actor(actor)
        return actor

    def save_actor(self, actor, limbo=False):
        if limbo:
            self._save_object(actor, "actors", _loadstate="limbo")
        else:
            self._save_object(actor, "actors")

    def update_actor(self, actor, **fields):
        self.dbase.update_object_fields("actors", actor, **fields)

    def update_room(self, room, **fields):
        self.dbase.update_object_fields("rooms", room, **fields)

    def room_exists(self, game_id, room_id):
        return self.dbase.object_exists("rooms", dict(game_id=game_id,
            room_id=room_id))

    def load_player(self, username, game_id):
        return self._load_filter_one("actors", dict(username=username,
            game_id=game_id, __type__="PlayerActor"))

    def load_players_for_room(self, game_id, room_id):
        return self._load_filter("actors", game_id=game_id, room_id=room_id,
            __type__="PlayerActor")

    def load_actor(self, actor_id):
        return self._load_filter_one("actors", dict(actor_id=actor_id))

    def load_limbo_actor(self, game_id, room_id):
        enc_actor = self.dbase.find_and_modify("actors",
            query={'game_id': game_id, 'room_id': room_id,
                   '_loadstate': "limbo", 'docked_with': None},
            update={"$set": {"_loadstate": ""}},
        )
        return self._decode_enc_dict(enc_actor) if enc_actor else None

    def load_docked_actors(self, game_id, parent_actor_id):
        object_dicts = self.dbase.filter("actors", dict(game_id=game_id,
            docked_with=parent_actor_id))
        objects = [self._decode_enc_dict(enc_dict) for enc_dict in object_dicts]
        return objects

    def save_player(self, player):
        self._save_object(player, "actors")

    def player_exists(self, username, game_id):
        return self.dbase.object_exists("actors", dict(username=username,
            game_id=game_id))

    def players_in_game(self, game_id):
        return self._find_players(game_id=game_id)

    def all_players_for(self, username):
        return self._find_players(username=username)

    def all_players(self):
        return self._find_players()

    def _find_players(self, **kwargs):
        return self._find_objects("actors", "PlayerActor", **kwargs)

    def _find_games(self, **kwargs):
        return self._find_objects("games", "Game", **kwargs)

    def _find_objects(self, collection, object_type, **kwargs):
        query = kwargs.copy()
        query['__type__'] = object_type
        object_dicts = self.dbase.filter(collection, query)
        objects = [self._decode_enc_dict(enc_dict) for enc_dict in object_dicts]
        return objects

    def load_game(self, game_id):
        return self._load_object(game_id, "games")

    def save_game(self, game):
        self._save_object(game, "games")

    def create_game(self, owner_id, name=None, description=None):
        game = Game(owner_id, name, description)
        self.save_game(game)
        return game

    def game_exists(self, game_id):
        return self.dbase.object_exists_by_id("games", game_id)

    def all_games(self):
        game_dicts = self.dbase.filter("games", {})
        games = [self._decode_enc_dict(enc_dict) for enc_dict in game_dicts]
        return games

    def games_owned_by(self, username):
        return self._find_games(owner_id=username)

    def create_player(self, room, actor_type, script, username, game_id):
        player = PlayerActor(room, actor_type, script, username,
            game_id=game_id)
        self.save_player(player)
        return player

    def remove_actor(self, actor_id):
        self._remove_queue.put(actor_id)

    def _run_remove_queue(self):
        while self._running:
            actor_id = self._remove_queue.get()
            if actor_id:
                log.debug("Removing actor: %s", actor_id)
                self.dbase.remove("actors", actor_id=actor_id)

    ## ---- Admin methods

    def list_nodes(self):
        return self._load_filter('online_nodes', {})

    def list_rooms(self, node_name=None):
        query = {}
        if node_name:
            query['node_name'] = node_name
        return self._load_filter('rooms', query)

    def list_games(self, owner_id=None, node_name=None):
        query = {}
        if owner_id:
            query['owner_id'] = owner_id
        if node_name:
            query['node_name'] = node_name
        return self._load_filter('games', query)

    def list_players(self, node_name=None):
        query = {'__type__': 'PlayerActor'}
        if node_name:
            query['node_name'] = node_name
        return self._load_filter('actors', query)

    ## ---- Encoding method

    def _save_object(self, saved_object, dbase_name, **fields):
        if getattr(saved_object, '_id', None):
            db_id = saved_object._id
            saved_object._id = None
        else:
            db_id = None
        object_dict = self._obj_to_dict(saved_object)
        object_dict.update(fields)
        db_id = self.dbase.save_object(object_dict, dbase_name, db_id)
        saved_object._id = str(db_id)
        return str(db_id)

    def _load_object(self, object_id, dbase_name):
        enc_dict = self.dbase.load_object(object_id, dbase_name)
        db_id = enc_dict.pop('_id')
        obj = self._dict_to_obj(enc_dict)
        obj._id = str(db_id)
        return obj

    def _obj_to_dict(self, pyobject):
        encoded_str = json.dumps(pyobject, default=self._encode, indent=4)
        return json.loads(encoded_str)

    def _dict_to_obj(self, obj_dict):
        obj_str = json.dumps(obj_dict)
        return json.loads(obj_str, object_hook=self._decode)

    def _encode(self, obj):
        obj_name =  type(obj).__name__
        if obj_name in self.serializers:
            data = self.serializers[obj_name](obj)
            data['__type__'] = obj_name
            return data
        raise TypeError("Cannot serialize object %s" % obj_name)

    def _decode(self, data):
        if "__type__" in data:
            obj_type = data.pop('__type__')
            if obj_type in self.builders:
                return self.builders[obj_type](data)
            else:
                raise TypeError("No such type:%s" % obj_type)
        return data

    def _load_filter_one(self, collection, query):
        enc_dict = self.dbase.filter_one(collection, query)
        if enc_dict:
            return self._decode_enc_dict(enc_dict)
        else:
            raise Exception("No such object in collection %s: %s" % (
                collection, query))

    def _load_filter(self, collection, query):
        enc_list = self.dbase.filter(collection, query)
        return [self._decode_enc_dict(enc) for enc in enc_list]

    def _decode_enc_dict(self, enc_dict):
        db_id = enc_dict.pop('_id')
        obj = self._dict_to_obj(enc_dict)
        obj._id = str(db_id)
        return obj

    ## -- encoding / decoding methods

    # Game
    def _serialize_game(self, game):
        return dict(owner_id=game.owner_id, name=game.name,
            description=game.description)

    def _build_game(self, data):
        game = Game(data['owner_id'], data.get("name"), data.get("description"))
        game.item_registry = self.item_registry
        return game

    # Position
    def _serialize_position(self, position):
        return dict(x=position.x, y=position.y, z=position.z)

    def _build_position(self, data):
        return Position(data['x'], data['y'], data['z'])

    # PlayerActor
    def _serialize_player(self, player):
        data = self._serialize_actor(player)
        data['status'] = player.status
        data['token'] = player.token
        data['timeout_time'] = player.timeout_time
        return data

    def _build_player(self, data):
        script = self.node.scripts[data['script_name']] if self.node else None
        player = PlayerActor(None, data['actor_type'],
            script, visible=data['visible'],
            username=data['username'], actor_id=data['actor_id'],
            room_id=data['room_id'], game_id=data['game_id'])
        player.parent_id = data['parent_id']
        player.state = data['state']
        player.state._set_actor(player)
        player.path = data['path']
        player.vector = data['vector']
        player._speed = data['speed']
        player._docked_with = data['docked_with']
        player.status = data['status']
        player.token = data.get('token')
        player.timeout_time = data.get('timeout_time')
        return player

    # Room
    def _serialize_room(self, room):
        return dict(game_id=room.game_id, room_id=room.room_id,
            state=room.state, last_modified=datetime.isoformat(
                datetime.utcfromtimestamp(Timer.now())),
            node_name=self.node.name, initialized=room.initialized)

    def _build_room(self, data):
        room = self.room_builder.create(data['game_id'], data['room_id'])
        room.state = data['state']
        room.initialized = data.get('initialized', False)
        room.geography = self.geography
        self.geography.setup(room)
        return room

    # Door
    def _serialize_door(self, door):
        return dict(exit_room_id=door.exit_room_id,
            enter_position=door.enter_position, exit_position=door.exit_position)

    def _build_door(self, data):
        return Door(data['exit_room_id'], data['enter_position'],
            data['exit_position'])

    # Actor
    def _serialize_actor(self, actor):
        return dict(actor_id=actor.actor_id,
            parent_id=actor.parent_id,
            state=actor.state,
            game_id=actor.game_id,
            room_id=actor.room_id,
            path=actor.path,
            vector=actor.vector,
            visible=actor.visible,
            script_name=actor.script.script_name,
            actor_type=actor.actor_type,
            username=actor.username,
            docked_with=actor.docked_with.actor_id if \
                actor.docked_with else None,
            speed=actor.speed)

    def _build_actor(self, data):
        script = self.node.scripts[data['script_name']] if self.node else None
        actor = Actor(None, data['actor_type'],
            script, visible=data['visible'],
            username=data['username'], actor_id=data['actor_id'],
            room_id=data['room_id'], game_id=data['game_id'])
        actor.parent_id = data['parent_id']
        actor.state = data['state']
        actor.state._set_actor(actor)
        actor.path = data['path']
        actor.vector = data['vector']
        actor._speed = data['speed']
        actor._docked_with = data['docked_with']
        return actor

    # Script
    def _serialize_script(self, script):
        return dict(script_name=script.script_name)

    def _build_script(self, data):
        script_name = data['script_name']
        return Script(script_name, self.node.scripts[script_name])

    # Vector
    def _serialize_vector(self, vector):
        return dict(start_pos=vector.start_pos, start_time=vector.start_time,
            end_pos=vector.end_pos, end_time=vector.end_time)

    def _build_vector(self, data):
        return Vector(data['start_pos'], data['start_time'], data['end_pos'],
            data['end_time'])

    # SyncDict
    def _serialize_syncdict(self, syncdict):
        return dict(syncdict._data)

    def _build_syncdict(self, data):
        syncdict = SyncDict()
        syncdict._data = data
        return syncdict

    # SyncList
    def _serialize_synclist(self, synclist):
        return dict(data=list(synclist._data))

    def _build_synclist(self, data):
        synclist = SyncList()
        synclist._data = data['data']
        return synclist

    # OnlineNode
    def _serialize_onlinenode(self, onlinenode):
        return dict(name=onlinenode.name, host=onlinenode.host,
            load=onlinenode.load, uptime=onlinenode.uptime)

    def _build_onlinenode(self, data):
        node = OnlineNode(name=data['name'], host=data['host'])
        node.load = data['load']
        node.uptime = data['uptime']
        return node

    def load_next_available_room(self):
        return self.dbase.find_and_modify("rooms",
            query={"_state":"pending",
                   sort:[('last_modified', pymongo.DESCENDING)]},
            update={"$set": {"_state": "active"}},
        )

    def load_node(self, name):
        return self._load_filter_one('online_nodes', dict(name=name))

    def save_node(self, online_node):
        self._save_object(online_node, "online_nodes")

    def onlinenode_update(self, name, host, load):
        return self.dbase.find_and_modify("online_nodes",
            query={"name": name},
            update={
                '$set':{
                    "host": host, "load": load, 'uptime': Timer.now(),
                },
                '$setOnInsert': {"name": name, "__type__": "OnlineNode"},
            },
            upsert=True,
            new=True,
        )

    def find_and_modify_object(self, collection_name, obj, query=None,
                               set_fields=None, set_on_insert=None,
                               upsert=False):
        ''' Will perform a find_and_modify on the collection. If upserting,
            will use the serialized form of the given obj as setOnInsert,
            otherwise will only set what's in set_fields
        '''
        set_fields = set_fields or {}
        set_on_insert = set_on_insert or {}

        if not query and hasattr(obj, '_id'):
            query = {'_id': bson.ObjectId(obj._id)}
        obj_data = self._obj_to_dict(obj)
        if set_on_insert:
            obj_data.update(set_on_insert)

        update = {}
        if set_fields:
            update['$set'] = set_fields
        if upsert:
            for key in set_fields:
                if key in obj_data:
                    obj_data.pop(key)
            update['$setOnInsert'] = obj_data
        new = self.dbase.find_and_modify(collection_name, query, update=update,
            upsert=upsert)
        return self._dict_to_obj(new)
