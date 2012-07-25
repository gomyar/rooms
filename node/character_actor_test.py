
import unittest

from character_actor import CharacterActor
from room import Room


class MockRollSystem:
    def roll(self, actor, stats):
        total = 0
        for stat in stats:
            total += actor.stats[stat]
        return total

class CharacterActorTest(unittest.TestCase):
    def setUp(self):
        self.actor = CharacterActor("actor1")
        self.actor.roll_system = MockRollSystem()
        self.actor.stats['str'] = 0.1
        self.actor.stats['brawl'] = 0.4
        self.room = Room()
        self.actor.room = self.room

    def testRoll(self):
        self.assertEquals(True, self.actor.roll(["str", "brawl"], 10))

    def testWalkTowards(self):
        self.actor2 = CharacterActor("actor2", (0, 0))
        self.actor2.room = self.room

        self.actor2.move_to(self.actor2, 10, 10)

        self.assertEquals([(0, 0), (10, 10)], self.actor2.path.basic_path_list())
