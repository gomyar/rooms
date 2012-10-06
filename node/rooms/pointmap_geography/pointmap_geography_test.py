
import unittest

from pointmap_geography import PointmapGeography
from rooms.room import Room
from rooms.room import RoomObject


class PointmapGeogTest(unittest.TestCase):
    def setUp(self):
        self.geog = PointmapGeography(point_spacing=10)
        self.room = Room("room1", (0, 0), 50, 50)

    def testGetPath(self):
        path = self.geog.get_path(self.room, (10, 10), (20, 20))
        self.assertEquals(25, len(self.geog._pointmaps[self.room]._points))
        self.assertEquals([(10, 10), (20, 20)], path)

        path = self.geog.get_path(self.room, (10, 10), (20, 40))
        self.assertEquals([(10, 10), (20, 20), (20, 30), (20, 40)], path)

        path = self.geog.get_path(self.room, (15, 15), (25, 45))
        self.assertEquals([(10, 10), (20, 20), (20, 30), (20, 40)], path)

    def testCreatePointMapRelativeToRoomCoords(self):
        self.room = Room("room1", (100, 200), 50, 50)

        path = self.geog.get_path(self.room, (10, 10), (20, 40))
        self.assertEquals([], path)

        path = self.geog.get_path(self.room, (110, 210), (120, 240))
        self.assertEquals([(110, 210), (120, 220), (120, 230), (120, 240)], path)

    def testRoomObjectsCreateBlankZones(self):
        self.room.add_object("table", RoomObject("table", 20, 20), (10, 10))

        self.assertEquals(16, len(self.geog._get_pointmap(self.room).available_points()))

    def testTwoRoomObjectsCreateBlankZones(self):
        self.room.add_object("table1", RoomObject("table", 20, 20), (0, 10))
        self.room.add_object("table2", RoomObject("table", 20, 20), (20, 10))

        self.assertEquals(10, len(self.geog._get_pointmap(self.room).available_points()))

    def testClosestPointToPosition(self):
        self.room.add_object("table", RoomObject("table", 20, 20), (10, 10))

        self.assertEquals((0, 0), self.geog.get_available_position_closest_to(
            self.room, (20, 20)))
