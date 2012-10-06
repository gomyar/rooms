
import unittest

from room import Room
from area import Area
from actor import Actor


class RoomTest(unittest.TestCase):
    def setUp(self):
        self.area = Area()
        self.area.rooms['room1'] = Room("room1", (0, 0), 100, 100)
        self.area.rooms['room1'].area = self.area
        self.area.rooms['room2'] = Room("room2", (100, 0), 100, 100)
        self.area.rooms['room2'].area = self.area
        self.area.rooms['room3'] = Room("room3", (0, 100), 100, 100)
        self.area.rooms['room3'].area = self.area

        self.area.create_door(self.area.rooms['room1'],
            self.area.rooms['room2'], (0, 0), (10, 0))
        self.area.create_door(self.area.rooms['room1'],
            self.area.rooms['room3'], (10, 0), (0, 0))

    def _mock_sleep(self, seconds):
        self._mock_slept_for = seconds

    def testDoorsExist(self):
        self.assertTrue(self.area.rooms['room1'].has_door_to("room2"))
        self.assertTrue(self.area.rooms['room1'].has_door_to("room3"))
        self.assertFalse(self.area.rooms['room3'].has_door_to("room2"))

    def testActorExitsThroughDoor(self):
        self.actor = Actor("actor1", (10, 10))
        self.actor.sleep = self._mock_sleep
        self.area.rooms['room1'].actor_joined_instance(self.actor)

        self.actor.move_to_room("room2")

        self.assertEquals([(100, 0), (100, 0)], self.actor.path.basic_path_list())
        self.assertEquals(0.47, round(self._mock_slept_for, 2))
