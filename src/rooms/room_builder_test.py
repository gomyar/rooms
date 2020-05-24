
import os
import unittest
import json

from rooms.testutils import MockNode
from rooms.room import Room
from rooms.room import Tag
from rooms.room_builder import RoomBuilder
from rooms.room_builder import FileMapSource
from rooms.position import Position


class RoomBuilderTest(unittest.TestCase):
    def setUp(self):
        self.node = MockNode()
        self.map_source = FileMapSource(os.path.join(os.path.dirname(__file__),
            "test_maps"))
        self.factory = RoomBuilder(self.map_source, self.node)

    def testCreateRoom(self):
        room = self.factory.create("game1", "map1.room1")

        self.assertEquals(1, len(room.room_objects))
        self.assertEquals("map1.room1", room.room_id)
        self.assertEquals("game1", room.game_id)
        self.assertEquals(Tag("tag.type.1", Position(25, 25),
            {"field1": "value1"}), room.tags[0])
        self.assertEquals(1, len(room.doors))
        self.assertEquals("map1.room2", room.doors[0].exit_room_id)
        self.assertEquals(0.0, room.doors[0].position.x)
        self.assertEquals(125.0, room.doors[0].position.y)
        self.assertEquals(0, room.room_objects[0].topleft.x)
        self.assertEquals(0, room.room_objects[0].topleft.y)
        self.assertEquals(90, room.room_objects[0].facing)
        self.assertEquals(False, room.room_objects[0].passable)

    def testCreateRoom2(self):
        room = self.factory.create("game1", "map1.room2")

        self.assertEquals(1, len(room.room_objects))
        self.assertEquals("map1.room2", room.room_id)
        self.assertEquals("game1", room.game_id)
        self.assertEquals(Tag("tag.type.1", Position(50, 50),
            {"field1": "value1"}), room.tags[0])
        self.assertEquals(1, len(room.doors))
        self.assertEquals("map1.room2", room.doors[0].exit_room_id)
        self.assertEquals(50.0, room.doors[0].position.x)
        self.assertEquals(25.0, room.doors[0].position.y)
        self.assertEquals(0, room.room_objects[0].topleft.x)
        self.assertEquals(0, room.room_objects[0].topleft.y)
        self.assertEquals(-90, room.room_objects[0].facing)

    def testNoSuchRoom(self):
        self.assertRaises(Exception, self.factory.create, "game1",
            "map1.nonexistant")
