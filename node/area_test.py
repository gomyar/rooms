
import unittest

from area import Area
from door import Door
from room import Room
from room_container import RoomContainer


class MockRoomContainer(RoomContainer):
    def load_room(self, room_id):
        return self._rooms[room_id]

    def save_room(self, room_id, room):
        self._rooms[room_id] = room


class AreaTest(unittest.TestCase):
    def setUp(self):
        self.area = Area()
        self.area.rooms = MockRoomContainer(self.area)
        self.room1 = Room("room1", (0, 0), 10, 10)
        self.room2 = Room("room2", (20, 0), 10, 10)

    def testAddDoor(self):
        self.area.create_door(self.room1, self.room2, (10, 5), (0, 5))

        self.assertEquals(Door("door_room2_10_5", (10, 5), self.room2,
            'door_room1_0_5'), self.room1.actors['door_room2_10_5'])
        self.assertEquals(Door("door_room1_0_5", (0, 5), self.room1,
            'door_room2_10_5'), self.room2.actors['door_room1_0_5'])

    def testAddDoorInferPosition(self):
        self.area.create_door(self.room1, self.room2)
        door1 = self.room1.all_doors()[0]
        door2 = self.room2.all_doors()[0]

        self.assertEquals((10, 5), door1.position())
        self.assertEquals((20, 5), door2.position())

        self.room1 = Room("room1", (20, 0), 10, 10)
        self.room2 = Room("room2", (20, 20), 10, 10)

        self.area.create_door(self.room1, self.room2)
        door1 = self.room1.all_doors()[0]
        door2 = self.room2.all_doors()[0]

        self.assertEquals((25, 10), door1.position())
        self.assertEquals((25, 20), door2.position())
