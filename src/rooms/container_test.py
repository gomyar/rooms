
import unittest

from collections import defaultdict

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


class MockDbaseConnection(object):
    def __init__(self):
        self.dbases = defaultdict(lambda: defaultdict(lambda: None))

    def load_object(self, object_id, dbase_name):
        return self.dbases[dbase_name][object_id]

    def save_object(self, saved_obj, dbase_name, object_id):
        self.dbases[dbase_name][object_id] = saved_obj

    def filter(self, dbase_name, search_fields):
        objs = dict()
        for key, obj in self.dbases[dbase_name].items():
            if set(search_fields.items()).issubset(\
                set(self.dbases[dbase_name].items())):
                objs[key] = obj
        return objs

    def object_exists(self, dbase_name, search_fields):
        return bool(self.filter(dbase_name, search_fields))


class ContainerTest(unittest.TestCase):
    def setUp(self):
        self.area = Area()
        self.area.load_script("container_test")
        self.area.instance = Null()
        self.room1 = Room('lobby')
        self.room1.area = self.area
        self.area.rooms['lobby'] = self.room1
        self.actor1 = Actor('actor1')
        self.actor1.room = self.room1
        self.area.rooms['lobby'].actors['actor1'] = self.actor1
        self.dbase = MockDbaseConnection()
        self.container = Container(self.dbase, LinearOpenGeography())

    def testSaveRoom(self):
        self.container.save_room(self.room1)

        # Why None? because mongo creates the id
        self.assertEquals('lobby', self.dbase.dbases['rooms'][None]['description'])

    def testSaveRoomWithPlayer(self):
        self.player = Player("bob")
        self.player_actor = PlayerActor(self.player)
        self.room1.put_actor(self.player_actor)

        self.container.save_room(self.room1)

        self.assertEquals('lobby', self.dbase.dbases['rooms'][None]['description'])
        self.assertEquals('bob', self.dbase.dbases['players'][None]['username'])

    def testGetOrCreatePlayer(self):
        self.assertEquals(None, self.container.load_player("nonexistant"))

        player = self.container.get_or_create_player("newplayer")
        self.assertEquals("newplayer", player.username)

    def testJsonPickle(self):
        pickled = self.container._serialize_area(self.area)
        unpickled = self.container._create_area(pickled)
        unpickled.rooms = MockRoomContainer(self.area)
        unpickled.rooms._rooms['lobby'] = Room('lobby')
        unpickled.rooms._rooms['lobby'].actors['actor1'] = Actor('actor1')
        self.assertEquals(self.area.rooms['lobby'], unpickled.rooms['lobby'])
        self.assertEquals(self.area.rooms['lobby'].actors['actor1'],
            unpickled.rooms['lobby'].actors['actor1'])
