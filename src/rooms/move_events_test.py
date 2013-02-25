
import unittest

from rooms.room import Room
from rooms.actor import Actor
from script import command
from rooms import waypoint


@command
def entered(actor, actor_entered):
    pass


class MoveEventsTest(unittest.TestCase):
    def setUp(self):
        waypoint.get_now = self._mock_get_now
        self._mock_now = 0

        self._updates = []

        self.room = Room()
        self.actor = Actor()
        self.actor.load_script("rooms.move_events_test")
        self.actor.sleep = self._mock_sleep
        self.actor.get_now = self._mock_get_now
        self.actor._update = self._mock_update

        self.actor2 = Actor()
        self.actor2.sleep = self._mock_sleep
        self.actor2.get_now = self._mock_get_now

        self.actor.set_visibility_range(10)

        self.room.put_actor(self.actor, (20, 20))
        self.room.put_actor(self.actor2, (5, 10))

        self.actor._update = self._mock_update

    def tearDown(self):
        reload(waypoint)

    def _mock_get_now(self):
        return self._mock_now

    def _mock_sleep(self, seconds):
        self._mock_now += seconds

    def _mock_update(self, update_id, **kwargs):
        self._updates.append((update_id, kwargs))

    def testMoveIntoRange(self):
        self.assertFalse(self.actor.can_see(self.actor2))

        self.actor2.move_to(15, 15)
        self.assertEquals((15, 15), self.actor2.position())

        self.assertTrue(self.actor.can_see(self.actor2))
        self.assertEquals([("actor_update", {})], self._updates)

    def testMoveOutOfRange(self):
        self.actor2.set_position((15, 15))

        self.assertTrue(self.actor.can_see(self.actor2))
        self.assertEquals([("actor_update", {})], self._updates)

        self.actor2.move_to(5, 10)

        self.assertEquals([("actor_update", {}), ("remove_actor", {})],
            self._updates)
