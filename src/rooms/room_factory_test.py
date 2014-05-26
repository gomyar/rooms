
import os
import unittest
import json

from rooms.testutils import MockNode
from rooms.room import Room
from rooms.room import Tag
from rooms.room_factory import RoomFactory
from rooms.position import Position


class RoomFactoryTest(unittest.TestCase):
    def setUp(self):
        self.node = MockNode()
        self.factory = RoomFactory(json.loads(open(os.path.join(
            os.path.dirname(__file__), "room_factory_test.json")).read()),
            self.node)


    def testCreateRoom(self):
        room = self.factory.create("room1", "game1")

        self.assertEquals(1, len(room.room_objects))
        self.assertEquals("room1", room.room_id)
        self.assertEquals("game1", room.game_id)
        self.assertEquals(Tag("tag.type.1", Position(25, 25),
            {"field1": "value1"}), room.tags[0])
