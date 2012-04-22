
import unittest

from area import Area
from door import Door
from room import Room

class AreaTest(unittest.TestCase):
    def setUp(self):
        self.area = Area()
        self.room1 = Room("room1", (0, 0), 10, 10)
        self.room2 = Room("room2", (10, 0), 10, 10)

    def testAddDoor(self):
        self.area.create_door(self.room1, self.room2, (10, 5), (0, 5))

        self.assertEquals(Door("door_room2_10_5", (10, 5), self.room2,
            'door_room1_0_5'), self.room1.actors['door_room2_10_5'])
        self.assertEquals(Door("door_room1_0_5", (0, 5), self.room1,
            'door_room2_10_5'), self.room2.actors['door_room1_0_5'])
