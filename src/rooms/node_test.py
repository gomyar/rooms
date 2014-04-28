
import unittest

from rooms.node import Node
from rooms.room import Room
from rooms.player import Player


class MockContainer(object):
    def __init__(self):
        self.rooms = {("game1", "room1"): Room()}
        self.players = {"bob1": Player("bob", "game1", "room1")}

    def load_room(self, game_id, room_id):
        return self.rooms[game_id, room_id]

    def load_player(self, player_id):
        return self.players[player_id]


class NodeTest(unittest.TestCase):
    def setUp(self):
        self.container = MockContainer()
        self.node = Node("10.10.10.1", 8000, self.container)
        self.node._create_token = lambda: "TOKEN1"

    def testManageRoom(self):
        self.node.manage_room("game1", "room1")

        self.assertEquals(1, len(self.node.rooms))

    def testPlayerJoins(self):
        token = self.node.player_joins("bob", "game1", "room1")
        self.assertEquals("TOKEN1", token)

        self.assertEquals(1, len(self.node.players))

