
import json
from datetime import datetime

from rooms.game import Game
from rooms.player import PlayerActor
from rooms.room import Room, Door
from rooms.position import Position
from rooms.actor import Actor
from rooms.script import Script
from rooms.vector import Vector
from rooms.state import SyncDict
from rooms.state import SyncList
from rooms.online_node import OnlineNode
from rooms.admin_token import AdminToken
from rooms.room_map import Map
from rooms.room_map import MapRoom
from rooms.timer import Timer


class GameFactory(object):
    def __init__(self, container):
        self.container = container
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
            AdminToken=self._serialize_admintoken,
            Map=self._serialize_map,
            MapRoom=self._serialize_maproom,
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
            AdminToken=self._build_admintoken,
            Map=self._build_map,
            MapRoom=self._build_maproom,
        )

    def obj_to_dict(self, pyobject):
        encoded_str = json.dumps(pyobject, default=self._encode, indent=4)
        return json.loads(encoded_str)

    def dict_to_obj(self, obj_dict):
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

    ## -- encoding / decoding methods

    # Game
    def _serialize_game(self, game):
        return dict(owner_id=game.owner_id, name=game.name,
            description=game.description)

    def _build_game(self, data):
        game = Game(data['owner_id'], data.get("name"), data.get("description"))
        game.item_registry = self.container.item_registry
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
        script = self.container.node.scripts[data['script_name']] if self.container.node else None
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
            node_name=self.container.node.name, initialized=room.initialized)

    def _build_room(self, data):
        room = self.container.room_builder.create(data['game_id'], data['room_id'])
        room.state = data['state']
        room.initialized = data.get('initialized', False)
        room.geography = self.container.geography
        self.container.geography.setup(room)
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
            speed=actor.speed,
            _loadstate=None)

    def _build_actor(self, data):
        script = self.container.node.scripts[data['script_name']] if self.container.node else None
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

    # AdminToken
    def _serialize_admintoken(self, admintoken):
        return dict(token=admintoken.token, game_id=admintoken.game_id,
                    room_id=admintoken.room_id, timeout_time=admintoken.timeout_time)

    def _build_admintoken(self, data):
        admintoken = AdminToken(token=data['token'], game_id=data['game_id'],
                                room_id=data['room_id'], timeout_time=data['timeout_time'])
        return admintoken

    # Map
    def _serialize_map(self, room_map):
        return dict(map_id=room_map.map_id, rooms=room_map.rooms)

    def _build_map(self, data):
        return Map(data['map_id'], data['rooms'])

    def _serialize_maproom(self, maproom):
        return dict(topleft=maproom.topleft, bottomright=maproom.bottomright,
            doors=maproom.doors, tags=maprooms.tags, room_objects=maprooms.room_objects)

    def _build_maproom(self, data):
        maproom = MapRoom()
        maproom.topleft = data['topleft']
        maproom.bottomright = data['bottomright']
        maproom.room_objects = data['room_objects']
        maproom.tags = data['tags']
        return maproom

