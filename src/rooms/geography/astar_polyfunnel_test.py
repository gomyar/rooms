
import unittest

from rooms.room import Room
from rooms.room import RoomObject
from rooms.position import Position as P
from rooms.testutils import MockNode
from .polygon_funnel import PolygonFunnelGeography


class AStarPolyFunnelTest(unittest.TestCase):
    def setUp(self):
        self.room = Room("game1", "room1", MockNode())
        self.room.coords(-50, -50, 50, 50)

        self.geography = PolygonFunnelGeography()

        self.room.room_objects.append(RoomObject("test", P(0, 0), 40, 40))
        self.room.geog = self.geography

        self.geography.setup(self.room)

    def test_path(self):
        self.assertEquals([], self.geography.find_path(self.room, P(-40, -40), P(40, 40)))
