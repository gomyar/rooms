
import unittest

class ScriptTest(unittest.TestCase):
    def setUp(self):
        self.script = Script()
        self.npc = Actor()
        self.player = Player()
        self.room = Room()

        self.room.actors['npc1'] = self.npc
        self.room.actors['player1'] = self.player

        self.script.npc = npc

    def testWalkTowardsNearestPlayer(self):
        self.script.walk_to_nearest_player()

        self.assertEquals([(0, 0), (10, 0)], self.npc.path)
