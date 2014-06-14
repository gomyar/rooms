import json

from rooms.game import Game
from rooms.player import PlayerActor
from rooms.room import Room, Door
from rooms.position import Position
from rooms.actor import Actor
from rooms.script import Script
from rooms.vector import Vector

import logging
log = logging.getLogger("rooms.container")


class Container(object):
    def __init__(self, dbase, geography, node, room_factory):
        self.dbase = dbase
        self.geography = geography
        self.node = node
        self.room_factory = room_factory
        self.serializers = dict(
            Game=self._serialize_game,
            PlayerActor=self._serialize_player,
            Room=self._serialize_room,
            Door=self._serialize_door,
            Position=self._serialize_position,
            Actor=self._serialize_actor,
            Vector=self._serialize_vector,
        )
        self.builders = dict(
            Game=self._build_game,
            PlayerActor=self._build_player,
            Room=self._build_room,
            Door=self._build_door,
            Position=self._build_position,
            Actor=self._build_actor,
            Vector=self._build_vector,
        )

    def load_room(self, game_id, room_id):
        room = self._load_filter_one("rooms", game_id=game_id, room_id=room_id)
        actors_list = self._load_filter("actors", game_id=game_id,
            room_id=room_id)
        for actor in actors_list:
            room.put_actor(actor)
        return room

    def save_room(self, room):
        self._save_object(room, "rooms")

    def create_room(self, game_id, room_id):
        if self.room_exists(game_id, room_id):
            raise Exception("Room %s %s already exists" % (game_id, room_id))
        room = self.room_factory.create(game_id, room_id)
        room.geography = self.geography
        self.save_room(room)
        return room

    def create_actor(self, room, actor_type, script_name, username=None):
        actor = Actor(room, actor_type, script_name, username)
        self.save_actor(actor)
        return actor

    def save_actor(self, actor):
        self._save_object(actor, "actors")

    def update_actor(self, actor, **fields):
        self.dbase.update_object_fields("actors", actor, **fields)

    def room_exists(self, game_id, room_id):
        return self.dbase.object_exists("rooms", game_id=game_id,
            room_id=room_id)

    def load_player(self, username, game_id):
        return self._load_filter_one("actors", username=username,
            game_id=game_id, __type__="PlayerActor")

    def load_actor(self, actor_id):
        return self._load_object(actor_id, "actors")

    def save_player(self, player):
        self._save_object(player, "actors")

    def player_exists(self, username, game_id):
        return self.dbase.object_exists("actors", username=username,
            game_id=game_id)

    def players_in_game(self, game_id):
        return self._find_players(game_id=game_id)

    def all_players(self):
        return self._find_players()

    def _find_players(self, **kwargs):
        player_dicts = self.dbase.filter("actors", __type__="PlayerActor",
            **kwargs)
        players = [self._decode_enc_dict(enc_dict) for enc_dict in player_dicts]
        return players

    def load_game(self, game_id):
        return self._load_object(game_id, "games")

    def save_game(self, game):
        self._save_object(game, "games")

    def create_game(self, owner_id):
        game = Game(owner_id)
        self.save_game(game)
        return game

    def game_exists(self, game_id):
        return self.dbase.object_exists_by_id("games", game_id)

    def all_games(self):
        game_dicts = self.dbase.filter("games")
        games = [self._decode_enc_dict(enc_dict) for enc_dict in game_dicts]
        return games

    def create_player(self, room, actor_type, script, username, game_id):
        player = PlayerActor(room, actor_type, script, username,
            game_id=game_id)
        self.save_player(player)
        return player

    ## ---- Encoding method

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

    def _load_filter_one(self, collection, **fields):
        enc_dict = self.dbase.filter_one(collection, **fields)
        if enc_dict:
            return self._decode_enc_dict(enc_dict)
        else:
            raise Exception("No such object in collection %s: %s" % (
                collection, fields))

    def _load_filter(self, collection, **fields):
        enc_list = self.dbase.filter(collection, **fields)
        return [self._decode_enc_dict(enc) for enc in enc_list]

    def _decode_enc_dict(self, enc_dict):
        db_id = enc_dict.pop('_id')
        obj = self._dict_to_obj(enc_dict)
        obj._id = str(db_id)
        return obj

    ## -- encoding / decoding methods

    # Game
    def _serialize_game(self, game):
        return dict(owner_id=game.owner_id)

    def _build_game(self, data):
        return Game(data['owner_id'])

    # Position
    def _serialize_position(self, position):
        return dict(x=position.x, y=position.y, z=position.z)

    def _build_position(self, data):
        return Position(data['x'], data['y'], data['y'])

    # PlayerActor
    def _serialize_player(self, player):
        data = self._serialize_actor(player)
        data['game_id'] = player.game_id
        return data

    def _build_player(self, data):
        script = self.node.scripts[data['script_name']] if self.node else None
        player = PlayerActor(None, data['actor_type'],
            script,
            data['username'], game_id=data['game_id'], actor_id=data['actor_id'],
            room_id=data['room_id'])
        player.state = data['state']
        player.path = data['path']
        player.vector = data['vector']
        player.speed = data['speed']
        return player

    # Room
    def _serialize_room(self, room):
        return dict(game_id=room.game_id, room_id=room.room_id,
            topleft=room.topleft, bottomright=room.bottomright,
            doors=room.doors)

    def _build_room(self, data):
        room = Room(data['game_id'], data['room_id'], data['topleft'],
            data['bottomright'], self.node)
        room.doors = data['doors']
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
            state=actor.state,
            game_id=actor.game_id,
            room_id=actor.room_id,
            path=actor.path,
            vector=actor.vector,
            script_name=actor.script.script_name,
            actor_type=actor.actor_type,
            username=actor.username,
            speed=actor.speed)

    def _build_actor(self, data):
        script = self.node.scripts[data['script_name']] if self.node else None
        actor = Actor(None, data['actor_type'],
            script,
            data['username'], actor_id=data['actor_id'],
            room_id=data['room_id'], game_id=data['game_id'])
        actor.state = data['state']
        actor.path = data['path']
        actor.vector = data['vector']
        actor.speed = data['speed']
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
