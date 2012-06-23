
import unittest

from character_actor import CharacterActor


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

    def testRoll(self):
        self.assertEquals(0.5, self.actor.roll(["str", "brawl"]))
