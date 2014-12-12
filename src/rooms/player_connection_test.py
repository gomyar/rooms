
import unittest

from rooms.testutils import MockRoom
from rooms.testutils import MockActor
from rooms.actor import Actor
from rooms.player_connection import PlayerConnection


class PlayerConnectionTest(unittest.TestCase):
    def setUp(self):
        self.room = MockRoom("game1", "room1")
        self.actor = Actor(self.room, "test", None)
        self.actor.room = self.room
        self.actor2 = Actor(self.room, "test", None)
        self.actor2.room = self.room
        self.conn = PlayerConnection("game1", "bob", self.room, self.actor,
            "TOKEN1")

