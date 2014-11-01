
import unittest

from pointmap_geography import PointmapGeography
from rooms.room import Room
from rooms.room import RoomObject
from rooms.position import Position
from rooms.testutils import MockNode


class PointmapGeogTest(unittest.TestCase):
    def setUp(self):
        self.geog = PointmapGeography(point_spacing=10)
        self.room = Room("game1", "room1", Position(0, 0), Position(50, 50),
            MockNode())

    def testGetPath(self):
        path = self.geog.find_path(self.room, (10, 10), (20, 20))
        self.assertEquals(25, len(self.geog._pointmaps[self.room]._points))
        self.assertEquals([(10, 10), (20, 20)], path)

        path = self.geog.find_path(self.room, (10, 10), (20, 40))
        self.assertEquals([(10, 10), (20, 20), (20, 30), (20, 40)], path)

        path = self.geog.find_path(self.room, (15, 15), (25, 45))
        self.assertEquals([(10, 10), (20, 20), (20, 30), (20, 40)], path)

    def testCreatePointMapRelativeToRoomCoords(self):
        self.room = Room("game1", "room1", Position(100, 200),
            Position(150, 250), MockNode())

        path = self.geog.find_path(self.room, (10, 10), (20, 40))
        self.assertEquals([], path)

        path = self.geog.find_path(self.room, (110, 210), (120, 240))
        self.assertEquals([(110, 210), (120, 220), (120, 230), (120, 240)], path)

    def testRoomObjectsCreateBlankZones(self):
        self.room.room_objects.append(RoomObject("table", Position(10, 10),
            Position(30, 30)))

        self.assertEquals(16, len(self.geog._get_pointmap(self.room).available_points()))

    def testTwoRoomObjectsCreateBlankZones(self):
        self.room.room_objects.append(RoomObject("table", Position(0, 10),
            Position(20, 30)))
        self.room.room_objects.append(RoomObject("table", Position(20, 10),
            Position(40, 30)))

        self.assertEquals(10, len(self.geog._get_pointmap(self.room).available_points()))

    def testClosestPointToPosition(self):
        self.room.room_objects.append(RoomObject("table", Position(10, 10),
            Position(30, 30)))

        self.assertEquals((0, 20), self.geog.get_available_position_closest_to(
            self.room, (20, 20)))
