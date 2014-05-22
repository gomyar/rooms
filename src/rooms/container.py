
import json

from rooms.game import Game
from rooms.player import Player
from rooms.room import Room
from rooms.position import Position
from rooms.actor import Actor
from rooms.script import Script
from rooms.vector import Vector

import logging
log = logging.getLogger("rooms.container")


class Container(object):
    def __init__(self, dbase, geography, node):
        self.dbase = dbase
        self.geography = geography
        self.node = node
        self.serializers = dict(
            Game=self._serialize_game,
            Player=self._serialize_player,
            Room=self._serialize_room,
            Position=self._serialize_position,
            Actor=self._serialize_actor,
            Script=self._serialize_script,
            Vector=self._serialize_vector,
        )
        self.builders = dict(
            Game=self._build_game,
            Player=self._build_player,
            Room=self._build_room,
            Position=self._build_position,
            Actor=self._build_actor,
            Script=self._build_script,
            Vector=self._build_vector,
        )

    def load_room(self, game_id, room_id):
        return self._load_filter("rooms", game_id=game_id, room_id=room_id)

    def save_room(self, room):
        self._save_object(room, "rooms")

    def create_room(self, game_id, room_id):
        room = Room(game_id, room_id, Position(0, 0), Position(10, 10),
            self.node)
        room.geography = self.geography
        self.save_room(room)
        return room

    def room_exists(self, game_id, room_id):
        return self.dbase.object_exists("rooms", game_id=game_id,
            room_id=room_id)

    def load_player(self, username, game_id):
        return self._load_filter("players", username=username, game_id=game_id)

    def save_player(self, player):
        self._save_object(player, "players")

    def player_exists(self, username, game_id):
        return self.dbase.object_exists("players", username=username,
            game_id=game_id)

    def players_in_game(self, game_id):
        return self._find_players(game_id=game_id)

    def all_players(self):
        return self._find_players()

    def _find_players(self, **kwargs):
        player_dicts = self.dbase.filter("players", **kwargs)
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

    def all_games(self):
        game_dicts = self.dbase.filter("games")
        games = [self._decode_enc_dict(enc_dict) for enc_dict in game_dicts]
        return games

    def create_player(self, username, game_id, room_id):
        player = Player(username, game_id, room_id)
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

    def _load_filter(self, collection, **fields):
        enc_dict = self.dbase.filter_one(collection, **fields)
        if enc_dict:
            return self._decode_enc_dict(enc_dict)
        else:
            raise Exception("No such object in collection %s: %s" % (
                collection, fields))

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

    # Player
    def _serialize_player(self, player):
        return dict(username=player.username,
            game_id=player.game_id,
            room_id=player.room_id)

    def _build_player(self, data):
        return Player(data['username'], data['game_id'], data['room_id'])

    # Room
    def _serialize_room(self, room):
        return dict(game_id=room.game_id, room_id=room.room_id,
            topleft=room.topleft, bottomright=room.bottomright,
            actors=room.actors)

    def _build_room(self, data):
        room = Room(data['game_id'], data['room_id'], data['topleft'],
            data['bottomright'], self.node)
        room.actors = data['actors']
        for actor in room.actors.values():
            actor.room = room
        room.geography = self.geography
        self.geography.setup(room)
        return room

    # Actor
    def _serialize_actor(self, actor):
        return dict(actor_id=actor.actor_id, state=actor.state,
            path=actor.path, vector=actor.vector, script=actor.script,
            actor_type=actor.actor_type, model_type=actor.model_type,
            player_username=actor.player_username)

    def _build_actor(self, data):
        actor = Actor(None)
        actor.state = data['state']
        actor.path = data['path']
        actor.vector = data['vector']
        actor.script = data['script']
        actor.actor_type = data['actor_type']
        actor.model_type = data['model_type']
        actor.player_username = data['player_username']
        return actor

    # Script
    def _serialize_script(self, script):
        return dict(script_module=script._script_module.__name__)

    def _build_script(self, data):
        script = Script()
        script.load_script(data['script_module'])
        return script

    # Vector
    def _serialize_vector(self, vector):
        return dict(start_pos=vector.start_pos, start_time=vector.start_time,
            end_pos=vector.end_pos, end_time=vector.end_time)

    def _build_vector(self, data):
        return Vector(data['start_pos'], data['start_time'], data['end_pos'],
            data['end_time'])
