
import unittest

from rooms.room import Room
from rooms.room import Door
from rooms.position import Position
from rooms.testutils import MockGeog
from rooms.testutils import MockNode
from rooms.testutils import MockActor
from rooms.testutils import MockContainer
from rooms.geography.basic_geography import BasicGeography
from rooms import actor
from rooms.player import PlayerActor


def created(actor):
    actor.state['created'] = True


class RoomTest(unittest.TestCase):
    def setUp(self):
        self.node = MockNode()
        self.node.container = MockContainer()
        self.room = Room("game1", "room1", Position(0, 0), Position(50, 50),
            self.node)
        self.geography = MockGeog()
        self.room.geography = self.geography
        actor._create_actor_id = lambda: "actor1"

    def tearDown(self):
        reload(actor)

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
        self.assertEquals(created, actor.script._script_module.created)
        self.assertEquals(self.room, actor.room)
        self.assertEquals(actor, self.room.actors['actor1'])
        self.assertEquals(None, actor.player_username)

        self.player = PlayerActor(self.room, "player", "rooms.room_test", "bob")
        actor2 = self.room.create_actor("mock_actor", "rooms.room_test",
            player=self.player)
        self.assertEquals("bob", actor2.player_username)

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
        self.actor = MockActor()
        self.room.actor_update(self.actor, {"path": []})

        self.assertEquals([(self.actor, {"path": []})], self.node._updates)

    def testActorEnterDoor(self):
        self.door = Door("room2", Position(5, 5), Position(10, 10))
        self.actor = MockActor("actor1")

        self.room.doors.append(self.door)
        self.room.actors["actor1"] = self.actor

        self.room.actor_enters(self.actor, self.door)

        self.assertEquals((self.actor, "game1", "room2", Position(10, 10)),
            self.node._updates[0])
        self.assertEquals({}, self.room.actors)
