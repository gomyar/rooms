
import unittest

from collections import defaultdict

from rooms.game import Game
from rooms.room import Room
from rooms.room_container import RoomContainer
from rooms.area import Area
from rooms.actor import Actor
from rooms.player import Player
from rooms.player_actor import PlayerActor

from rooms.container import Container
from rooms.geography.linearopen_geography import LinearOpenGeography

from rooms.null import Null


class MockRoomContainer(RoomContainer):
    def load_room(self, room_id):
        return self._rooms[room_id]

    def save_room(self, room_id, room):
        self._rooms[room_id] = room


class MockDbase(object):
    def __init__(self):
        self.dbases = dict()

    def load_object(self, obj_id, dbase_name):
        return self.dbases.get(dbase_name, dict()).get(obj_id).copy()

    def save_object(self, obj_dict, dbase_name, db_id):
        obj_dict = obj_dict.copy()
        if dbase_name not in self.dbases:
            self.dbases[dbase_name] = dict()
        db_id = db_id or dbase_name + "_" + str(len(self.dbases[dbase_name]))
        obj_dict['_id'] = db_id
        self.dbases[dbase_name][db_id] = obj_dict
        return db_id

    def filter(self, dbase_name, **fields):
        found = self.dbases.get(dbase_name, dict()).values()
        found = [o for o in found if all([i in o.items() for i in fields.items()])]
        found = [o.copy() for o in found]
        return found

    def filter_one(self, dbase_name, **fields):
        result = self.filter(dbase_name, **fields)
        return result[0] if result else None

    def object_exists(self, dbase_name, **search_fields):
        return bool(self.filter(dbase_name, **search_fields))

    def remove(self, dbase_name, **fields):
        dbase = self.dbases.get(dbase_name, [])
        keep = dict()
        for k, v in dbase.items():
            if not all([i in v.items() for i in fields.items()]):
                keep[k] = v
        self.dbases[dbase_name] = keep


class ContainerTest(unittest.TestCase):
    def setUp(self):
        self.area = Area()
        self.area.load_script("rooms.container_test")
        self.area.rooms = RoomContainer(self.area, Null())
        self.area.server = Null()
        self.room1 = Room('lobby')
        self.room1.area = self.area
        self.area.rooms['lobby'] = self.room1
        self.actor1 = Actor('actor1')
        self.actor1.room = self.room1
        self.area.rooms['lobby'].actors['actor1'] = self.actor1
        self.dbase = MockDbase()
        self.container = Container(self.dbase, LinearOpenGeography())

    def testSaveRoom(self):
        self.container.save_room(self.room1)

        # Why None? because mongo creates the id
        self.assertEquals('lobby', self.dbase.dbases['rooms']['rooms_0']['description'])

    def testSaveRoomWithPlayer(self):
        self.player = Player("bob", "game1")
        self.player_actor = PlayerActor(self.player)
        self.room1.put_actor(self.player_actor)

        self.container.save_room(self.room1)

        self.assertEquals('lobby', self.dbase.dbases['rooms']['rooms_0']['description'])
        self.assertEquals('bob', self.dbase.dbases['players']['players_0']['username'])

    def testGetOrCreatePlayer(self):
        self.assertEquals(None, self.container.load_player("nonexistant",
            "game1"))

        player = self.container.get_or_create_player("newplayer", "game1")
        self.assertEquals("newplayer", player.username)

    def testJsonPickle(self):
        pickled = self.container._serialize_area(self.area)
        unpickled = self.container._create_area(pickled)
        unpickled.rooms = RoomContainer(self.area, Null())
        unpickled.rooms['lobby'] = Room('lobby')
        unpickled.rooms['lobby'].actors['actor1'] = Actor('actor1')
        self.assertEquals(self.area.rooms['lobby'], unpickled.rooms['lobby'])
        self.assertEquals(self.area.rooms['lobby'].actors['actor1'],
            unpickled.rooms['lobby'].actors['actor1'])

    def testDeleteGame(self):
        game = Game("bob")
        area1 = game.create_area("area1")
        area2 = game.create_area("area2")

        room1 = area1.create_room("room1", (10, 10))
        room2 = area1.create_room("room2", (40, 40))

        room3 = area2.create_room("room3", (40, 40))

        actor1 = room1.create_actor("test", "rooms.container_test")

        self.container.save_game(game)

        self.assertEquals("games_0", game.game_id)
        self.assertEquals(1, len(self.dbase.dbases['games']))
        self.assertEquals(2, len(self.dbase.dbases['areas']))
        self.assertEquals(3, len(self.dbase.dbases['rooms']))

        self.container.delete_game(game.game_id)
        self.assertEquals(0, len(self.dbase.dbases['games']))
        self.assertEquals(0, len(self.dbase.dbases['areas']))
        self.assertEquals(0, len(self.dbase.dbases['rooms']))
