
import unittest

from rooms.room import Room
from rooms.room import Door
from rooms.position import Position
from rooms.testutils import MockGeog
from rooms.testutils import MockNode
from rooms.testutils import MockActor
from rooms.testutils import MockContainer
from rooms.geography.basic_geography import BasicGeography
from rooms.player import PlayerActor
from rooms.script import Script


class RoomTest(unittest.TestCase):
    def setUp(self):
        self.script = Script("room_test", RoomTest)
        self.node = MockNode()
        self.node.scripts['rooms.room_test'] = self.script
        self.node.container = MockContainer()
        self.room = Room("game1", "room1", Position(0, 0), Position(50, 50),
            self.node)
        self.geography = MockGeog()
        self.room.geography = self.geography

    @staticmethod
    def created(actor):
        actor.state['created'] = True

    def testInitialSetup(self):
        self.assertEquals(50, self.room.width)
        self.assertEquals(50, self.room.height)
        self.assertEquals(Position(0, 0, 0), self.room.topleft)
        self.assertEquals(Position(50, 50, 0), self.room.bottomright)
        self.assertEquals(Position(25, 25, 0), self.room.center)

    def testCreateActor(self):
        actor = self.room.create_actor("mock_actor", "rooms.room_test")
        self.assertTrue(actor.state.created)
        self.assertFalse(actor._gthread is None)
        self.assertEquals(RoomTest.created, actor.script.script_module.created)
        self.assertEquals(self.room, actor.room)
        self.assertEquals(actor, self.room.actors['actors_0'])
        self.assertEquals(None, actor.username)

        self.player = PlayerActor(self.room, "player", "rooms.room_test", "bob")
        actor2 = self.room.create_actor("mock_actor", "rooms.room_test",
            player=self.player)
        self.assertEquals("bob", actor2.username)
        self.assertEquals(self.script, actor.script)

    def testFindPath(self):
        path = self.room.find_path(Position(1, 2), Position(3, 4))
        self.assertEquals([
            Position(1, 2), Position(3, 4),
        ], path)

    def testBasicGeography(self):
        geography = BasicGeography()
        self.room.geography = geography
        geography.setup(self.room)

        self.assertEquals(
            [Position(10, 20), Position(30, 40)],
            self.room.find_path(Position(10, 20), Position(30, 40)))

    def testActorUpdate(self):
        self.actor = MockActor("actor1")
        self.room.actor_update(self.actor, {"path": []})

        self.assertEquals([(self.room, "actor1", {"path": []})],
            self.node._updates)

    def testActorEnterDoor(self):
        self.door = Door("room2", Position(5, 5), Position(10, 10))
        self.actor = MockActor("actor1")

        self.room.doors.append(self.door)
        self.room.actors["actor1"] = self.actor

        self.room.actor_enters(self.actor, self.door)

        self.assertEquals((self.actor, "game1", "room2", Position(10, 10)),
            self.node._updates[0])

    def testActorAddRemove(self):
        newactor1 = MockActor("new1")
        self.room.put_actor(newactor1, Position(5, 5))

        self.assertEquals(1, len(self.room.actors))
        self.assertEquals("new1", self.room.actors.values()[0].actor_id)
        self.assertEquals(Position(5, 5), self.room.actors['new1'].vector.start_pos)
        self.assertEquals(Position(5, 5), self.room.actors['new1'].vector.end_pos)
