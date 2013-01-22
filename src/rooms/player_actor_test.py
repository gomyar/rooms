
import unittest

from player_actor import PlayerActor
from player import Player

class PlayerActorTest(unittest.TestCase):
    def setUp(self):
        self.player1 = Player("player1")
        self.player2 = Player("player2")
        self.player_actor1 = PlayerActor(self.player1)
        self.player_actor2 = PlayerActor(self.player2)

    def testMethodAccess(self):
        self.assertFalse(self.player_actor1._can_call(self.player_actor2,
            "state"))
        self.assertEquals([], self.player_actor1.exposed_methods(
            self.player_actor2))
