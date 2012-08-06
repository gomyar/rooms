
import unittest

from player_actor import PlayerActor

class PlayerActorTest(unittest.TestCase):
    def setUp(self):
        self.player_actor1 = PlayerActor("player1", (10, 10))
        self.player_actor2 = PlayerActor("player2", (10, 10))

    def testMethodAccess(self):
        self.assertFalse(self.player_actor1._can_call(self.player_actor2, "state"))
        self.assertEquals([], self.player_actor1.exposed_methods(
            self.player_actor2))

#        self.player_actor1.command_call("walk_to", 10, 10)
