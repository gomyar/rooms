
import unittest

from player_actor import PlayerActor
from instance import Instance

class PlayerActorTest(unittest.TestCase):
    def setUp(self):
        self.instance = Instance()
        self.player_actor1 = PlayerActor("player1")
        self.player_actor2 = PlayerActor("player2")

    def testMethodAccess(self):
        self.assertFalse(self.player_actor1._can_call(self.player_actor2,
            "state"))
        self.assertEquals([], self.player_actor1.exposed_methods(
            self.player_actor2))
