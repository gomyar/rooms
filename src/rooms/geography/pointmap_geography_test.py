
import unittest

from pointmap_geography import PointmapGeography
from rooms.room import Room
from rooms.room import RoomObject
from rooms.position import Position
from rooms.testutils import MockNode


class PointmapGeogTest(unittest.TestCase):
    def setUp(self):
        self.geog = PointmapGeography(point_spacing=10)
        self.room = Room("game1", "room1", MockNode())
        self.room.coords(0, 0, 50, 50)

    def testGetPath(self):
        self.geog = PointmapGeography(point_spacing=10)
        self.room = Room("game1", "room1", MockNode())
        self.room.coords(0, 0, 100, 100)

        path = self.geog.find_path(self.room, Position(10, 10), Position(20, 20))
        self.assertEquals(100, len(self.geog._pointmaps[self.room]._points))
        self.assertEquals([Position(10, 10), Position(10, 10), Position(20, 20)], path)

        path = self.geog.find_path(self.room, Position(10, 10), Position(20, 40))
        self.assertEquals([Position(10, 10), Position(10, 10), Position(20, 20), Position(20, 30), Position(20, 40)], path)

        path = self.geog.find_path(self.room, Position(15, 15), Position(25, 45))
        self.assertEquals([Position(10, 10), Position(10, 10), Position(20, 20), Position(20, 30), Position(20, 40)], path)

    def testGetPath2(self):
        self.geog = PointmapGeography(point_spacing=10)
        self.room = Room("game1", "room1", MockNode())
        self.room.coords(0, 0, 100, 100)

        path = self.geog.find_path(self.room, Position(11, 11), Position(22, 22))
        self.assertEquals(100, len(self.geog._pointmaps[self.room]._points))
        self.assertEquals([Position(10, 10), Position(10, 10),
                           Position(20, 20)], path)

        path = self.geog.find_path(self.room, Position(10, 10), Position(20, 40))
        self.assertEquals([Position(10, 10), Position(10, 10), Position(20, 20), Position(20, 30), Position(20, 40)], path)

        path = self.geog.find_path(self.room, Position(15, 15), Position(25, 45))
        self.assertEquals([Position(10, 10), Position(10, 10), Position(20, 20), Position(20, 30), Position(20, 40)], path)

    def testRoomObjectsCreateBlankZones(self):
        self.room.room_objects.append(RoomObject("table", Position(20, 20),
            20, 20))

        self.assertEquals(21, len(self.geog._get_pointmap(self.room).available_points()))

    def testTwoRoomObjectsCreateBlankZones(self):
        self.room.room_objects.append(RoomObject("table", Position(10, 20),
            20, 20))
        self.room.room_objects.append(RoomObject("table", Position(30, 20),
            20, 20))

        self.assertEquals(19, len(self.geog._get_pointmap(self.room).available_points()))

    def testClosestPointToPosition(self):
        self.room.room_objects.append(RoomObject("table", Position(20, 20),
            20, 20))

        self.assertEquals((0, 20), self.geog.get_available_position_closest_to(
            self.room, (20, 20)))
