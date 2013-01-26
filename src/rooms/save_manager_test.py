
import unittest

from rooms.save_manager import SaveManager
from rooms.area import Area
from rooms.room import Room
from rooms.player_actor import PlayerActor
from rooms.player import Player
from rooms.null import Null
from rooms.room_container import RoomContainer


class MockContainer(object):
    def __init__(self):
        self.saved = []

    def load_room(self, room_id):
        pass

    def save_room(self, room):
        self.saved.append(room)

    def save_player(self, player):
        self.saved.append(player)

class MockNode(object):
    def __init__(self):
        self.areas = dict()


class SaveManagerTest(unittest.TestCase):
    def setUp(self):
        self.node = MockNode()
        self.area = Area()
        self.area.server = Null()
        self.room1 = Room("room1")
        self.area.rooms['room1'] = self.room1
        self.room1.area = self.area
        self.node.areas[self.area.area_id] = self.area

        self.container = MockContainer()
        self.manager = SaveManager(self.node, self.container)

    def testSaveAllRoomsNoPlayers(self):
        self.manager.run_save()

        self.assertEquals([self.room1], self.container.saved)
        self.assertEquals([], self.area.rooms.values())


    def testSaveAllRoomsOnePlayers(self):
        player = Player("bob")
        player_actor = PlayerActor(player)
        self.room1.put_actor(player_actor)

        self.manager.run_save()

        self.assertEquals([self.room1, player], self.container.saved)
        self.assertEquals([self.room1], self.area.rooms.values())

    def testSaveWithPlayer(self):
        player = Player("bob")
        player_actor = PlayerActor(player)
        self.room1.put_actor(player_actor)

        self.manager.run_save()

        self.assertEquals([self.room1, player], self.container.saved)

    def testShutdown(self):
        player = Player("bob")
        player_actor = PlayerActor(player)
        self.room1.put_actor(player_actor)

        self.room2 = Room("room2")
        self.area.rooms['room2'] = self.room2
        self.room2.area = self.area

        player2 = Player("bob")
        player_actor2 = PlayerActor(player2)
        self.room2.put_actor(player_actor2)

        self.manager.start()
        self.manager.shutdown()

        self.assertEquals(set([self.room1, player, self.room2, player2]),
            set(self.container.saved))
        self.assertEquals([], self.area.rooms.values())
