
import unittest

from area import Area
from door import Door
from room import Room
from room_container import RoomContainer
from player_actor import PlayerActor


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
        self.room1.area = self.area
        self.room2 = Room("room2", (20, 0), 10, 10)
        self.room2.area = self.area
        self.area.rooms._rooms['room1'] = self.room1
        self.area.rooms._rooms['room2'] = self.room2

    def testBuildAreaMap(self):
        self.area.create_door(self.room1, self.room2, (10, 5), (0, 5))
        self.area.rebuild_area_map()

        self.assertEquals({(25, 5): [(5, 5)], (5, 5): [(25, 5)]},
            self.area.area_map)

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

    def testPlayerJoinsArea(self):
        self.area.player_script = "rooms.area_test"

        self.player = PlayerActor("player1")

        self.area.player_joined_instance(self.player, "room1")

        self.assertEquals("rooms.area_test",
            self.player.script.script_module.__name__)
