
import unittest

from area import Area
from door import Door
from room import Room
from player import Player
from room_container import RoomContainer
from player_actor import PlayerActor
from instance import Instance
from rooms.null import Null


class MockRoomContainer(RoomContainer):
    def load_room(self, room_id):
        return self._rooms[room_id]

    def save_room(self, room_id, room):
        self._rooms[room_id] = room


class AreaTest(unittest.TestCase):
    def setUp(self):
        self.area = Area()
        self.instance = Instance()
        self.area.instance = self.instance
        self.area.rooms = MockRoomContainer(self.area, Null())
        self.room1 = Room("room1", 10, 10)
        self.area.put_room(self.room1, (0, 0))
        self.room2 = Room("room2", 10, 10)
        self.area.put_room(self.room2, (20, 0))
        self.area.rooms['room1'] = self.room1
        self.area.rooms['room2'] = self.room2

    def testBuildAreaMap(self):
        self.room3 = Room("room3", 10, 10)
        self.area.put_room(self.room3, (30, 0))
        self.room3.area = self.area
        self.area.rooms._rooms['room3'] = self.room3
        self.area.create_door(self.room1, self.room2, (10, 5), (0, 5))
        self.area.create_door(self.room2, self.room3, (10, 5), (0, 5))
        self.area.rebuild_area_map()

        self.assertEquals(3, len(self.area.point_map._points))
        self.assertEquals([(25, 5)], self.area.point_map[(5, 5)].\
            connected_points())

        self.assertEquals(["room1", "room2"], self.area.find_path_to_room(
            "room1", "room2"))
        self.assertEquals(["room1", "room2", "room3"],
            self.area.find_path_to_room("room1", "room3"))

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

        self.room1 = Room("room1", 10, 10)
        self.area.put_room(self.room1, (20, 0))
        self.room2 = Room("room2", 10, 10)
        self.area.put_room(self.room2, (20, 20))

        self.area.create_door(self.room1, self.room2)
        door1 = self.room1.all_doors()[0]
        door2 = self.room2.all_doors()[0]

        self.assertEquals((25, 10), door1.position())
        self.assertEquals((25, 20), door2.position())
