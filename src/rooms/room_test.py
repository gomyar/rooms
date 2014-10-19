
import unittest

from rooms.room import Room
from rooms.room import Door
from rooms.room import Tag
from rooms.position import Position
from rooms.testutils import MockGeog
from rooms.testutils import MockNode
from rooms.testutils import MockActor
from rooms.testutils import MockContainer
from rooms.testutils import MockIDFactory
from rooms.geography.basic_geography import BasicGeography
from rooms.player import PlayerActor
from rooms.script import Script
from rooms.testutils import MockPlayerConnection


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
        MockIDFactory.setup_mock()

    def tearDown(self):
        MockIDFactory.teardown_mock()

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
        self.assertFalse(actor._script_gthread is None)
        self.assertEquals(RoomTest.created, actor.script.script_module.created)
        self.assertEquals(self.room, actor.room)
        self.assertEquals(actor, self.room.actors['id1'])
        self.assertEquals(None, actor.username)

        self.player = PlayerActor(self.room, "player", "rooms.room_test", "bob")
        actor2 = self.room.create_actor("mock_actor", "rooms.room_test",
            player=self.player)
        self.assertEquals("bob", actor2.username)
        self.assertEquals(self.script, actor.script)

        actor = self.room.create_actor("mock_actor", "rooms.room_test",
            position=Position(10, 10))
        self.assertEquals(actor.position, Position(10, 10))

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
        self.room.put_actor(self.actor, Position(10, 10))

        conn = MockPlayerConnection(self.actor)

        self.room.visibility.add_listener(conn)

        self.room.actor_state_changed(self.actor)
        self.assertEquals([("actor_state_changed", self.actor)], conn.messages)

        self.room.actor_becomes_invisible(self.actor)
        self.assertEquals([("actor_state_changed", self.actor),
            ("actor_becomes_invisible", self.actor)], conn.messages)

        self.room.actor_becomes_visible(self.actor)
        self.assertEquals([
            ("actor_state_changed", self.actor),
            ("actor_becomes_invisible", self.actor),
            ("actor_becomes_visible", self.actor),
        ], conn.messages)

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
        self.assertEquals([('kickoff', (newactor1,), {})],
            newactor1.script.called)

    def testSendRemoveUpdateOnRemoveActor(self):
        newactor1 = MockActor("new1")
        listener = MockActor("listener1")
        self.room.put_actor(newactor1, Position(5, 5))
        self.room.put_actor(listener, Position(1, 1))
        conn = MockPlayerConnection(listener)

        self.room.visibility.add_listener(conn)

        self.room.remove_actor(newactor1)

        self.assertEquals([("actor_removed", newactor1)], conn.messages)

    def testFindTags(self):
        tag1 = Tag("tag.room.1", Position(0, 0), {"field": "1"})
        tag2 = Tag("tag.room.2", Position(0, 0), {"field": "2"})
        tag3 = Tag("tag.something", Position(0, 0), {"field": "3"})

        self.room.tags = [tag1, tag2, tag3]

        self.assertEquals([tag1, tag2], self.room.find_tags("tag.room"))
        self.assertEquals([tag2], self.room.find_tags("tag.room.2"))
        self.assertEquals([tag3], self.room.find_tags("tag.something"))

        self.assertEquals([tag1, tag2, tag3], self.room.find_tags("tag"))
        self.assertEquals([tag1, tag2, tag3], self.room.find_tags(""))

    def testSplitPathBasedOnVisionGridWidth(self):
        self.room.visibility.gridsize = 10

        path = self.room.find_path(Position(10, 10), Position(20, 10))
        self.assertEquals([Position(10, 10), Position(20, 10)], path)

        path = self.room.find_path(Position(10, 10), Position(30, 10))
        self.assertEquals([Position(10, 10), Position(20, 10), Position(30, 10)], path)


    def testActorsAddedToRoomOutsideBoundariesArePositionedInside(self):
        newactor1 = MockActor("new1")
        self.room.put_actor(newactor1, Position(-5, -5))
        self.assertEquals(Position(0, 0), newactor1.position)

        newactor2 = MockActor("new1")
        self.room.put_actor(newactor2, Position(55, 55))
        self.assertEquals(Position(50, 50), newactor2.position)

    def testFindPathCorrectPosition(self):
        path = self.room.find_path(Position(-1, -2), Position(3, 4))
        self.assertEquals([
            Position(0, 0), Position(3, 4),
        ], path)

