
import unittest

from rooms.actor import Actor
from rooms.room import Room
from rooms.position import Position
from rooms.testutils import MockTimer
from rooms.testutils import MockGeog
from rooms.testutils import MockIDFactory
from rooms.testutils import MockGridVision
from rooms.testutils import MockNode
from rooms.testutils import MockContainer
from rooms.timer import Timer
from rooms.vector import Vector
from rooms.vector import create_vector
from rooms.room import Door
from rooms import actor
from rooms.script import Script


class ActorTest(unittest.TestCase):
    def setUp(self):
        MockTimer.setup_mock()
        MockIDFactory.setup_mock()
        self.node = MockNode()
        self.node.container = MockContainer()
        self.node.scripts['actor_script'] = Script("actor_script", ActorTest)
        self.room = Room("game1", "map1.room1", Position(0, 0),
            Position(100, 100), self.node)
        self.room.geography = MockGeog()
        self.actor = Actor(self.room, "mock_actor", Script("actor_script",
            ActorTest))
        self.room.put_actor(self.actor)
        self.actor.state.log = []
        self.vision = MockGridVision()
        self.room.vision = self.vision

    def tearDown(self):
        MockTimer.teardown_mock()
        MockIDFactory.teardown_mock()

    @staticmethod
    def created(actor):
        actor.state.log = []

    @staticmethod
    def kickoff(actor):
        actor.state.log.append('a')
        Timer.sleep(1)
        actor.state.log.append('b')
        Timer.sleep(1)
        actor.state.log.append('c')

    def action_to_perform(self, actor, *args, **kwargs):
        actor.state.val1 = args[0]

    def testActionMethod(self):
        self.actor.action(self.action_to_perform, "val1")
        self.assertEquals(None, self.actor.state.val1)
        MockTimer.fast_forward(0)
        self.assertEquals("val1", self.actor.state.val1)

    def testCreation(self):
        self.assertEquals(Vector(Position(0, 0), 0, Position(0, 0), 0),
            self.actor.vector)
        self.assertEquals("actor_script", self.actor.script.script_name)

    def testActorId(self):
        actor1 = Actor(self.room, "mock_actor", "rooms.actor_test", None)
        self.assertEquals("id2", actor1.actor_id)

        actor2 = Actor(self.room, "mock_actor", "rooms.actor_test",
            actor_id="actor2")
        self.assertEquals("actor2", actor2.actor_id)

    def testKickoff(self):
        self.actor.kick()
        self.assertEquals([], self.actor.state.log)

        MockTimer.fast_forward(1)

        self.assertEquals(['a', 'b'], self.actor.state.log)
        self.assertEquals(1, Timer.now())

        MockTimer.fast_forward(1)

        self.assertEquals(['a', 'b', 'c'], self.actor.state.log)
        self.assertEquals(2, Timer.now())

    def testSetPath(self):
        self.assertEquals(Position(0, 0), self.actor.position)

        self.actor.move_to(Position(10, 0))

        self.assertEquals([
            Position(0, 0),
            Position(10, 0),
        ], self.actor.path)

        self.assertEquals([
            ("actor_vector_changed", self.actor)
        ], self.vision.messages)

        MockTimer.fast_forward(1)

        self.assertEquals([
            ("actor_vector_changed", self.actor),
            ("actor_vector_changed", self.actor),
            ],
            self.vision.messages)

        self.assertEquals(Position(1.0, 0), self.actor.position)

    def testMoveToSpecifyPath(self):
        self.assertEquals(Position(0, 0), self.actor.position)

        self.actor.move_to(Position(10, 0), [Position(0, 0), Position(5, 0),
            Position(10, 0)])

        self.assertEquals([
            Position(0, 0),
            Position(5, 0),
            Position(10, 0),
        ], self.actor.path)

        MockTimer.fast_forward(1)

        self.assertEquals([
            ("actor_vector_changed", self.actor),
            ("actor_vector_changed", self.actor),
            ],
            self.vision.messages)

        MockTimer.fast_forward(5)

        self.assertEquals([
            ("actor_vector_changed", self.actor),
            ("actor_vector_changed", self.actor),
            ("actor_vector_changed", self.actor),
            ],
            self.vision.messages)

    def testSpeed(self):
        self.actor.speed = 2

        self.actor.move_to(Position(10, 0), [Position(0, 0), Position(5, 0),
            Position(10, 0)])

        self.assertEquals([
            Position(0, 0),
            Position(5, 0),
            Position(10, 0),
        ], self.actor.path)

        MockTimer.fast_forward(1)

        self.assertEquals([
            ("actor_vector_changed", self.actor),
            ("actor_vector_changed", self.actor),
            ],
            self.vision.messages)

    def testMoveWait(self):
        self.assertEquals(Position(0, 0), self.actor.position)

        self.actor.move_wait(Position(10, 0))

        self.assertEquals([
        #    Position(0, 0),
            Position(10, 0),
        ], self.actor.path)

        MockTimer.fast_forward(1)

        self.assertEquals(Position(1, 0), self.actor.position)

    def testActorEnters(self):
        door = Door("room2", Position(0, 0), Position(10, 10))
        self.actor.enter(door)

        self.assertEquals(('actor_removed', self.actor),
            self.vision.messages[0])

    def testDocking(self):
        self.actor2 = Actor(self.room, "mock_actor", Script("actor_script",
            ActorTest))
        self.actor2.state.log = []
        self.actor2.room = self.room

        self.actor2.dock_with(self.actor)

        self.assertEquals(set([self.actor2]), self.actor.docked_actors)
        self.assertEquals(self.actor, self.actor2.docked_with)

        self.assertEquals(Position(0, 0), self.actor.position)

        self.actor.move_to(Position(10, 0))

        expected_vector = create_vector(Position(0, 0), Position(10.0, 0), 1)
        MockTimer.fast_forward(1)

        self.assertEquals(Position(1.0, 0), self.actor.position)
        self.assertEquals(Position(1.0, 0), self.actor2.position)

        self.assertEquals(expected_vector, self.actor.vector)
        self.assertEquals(expected_vector, self.actor2.vector)

    def testMultiLayeredDockingVisibility(self):
        # test if a is docked with b is docked with c that:
        # c is visible to all
        # b is invisible to all, but visible to a
        # a is invisible to all, but visible to a
        self.fail("todo")

    def testMultiLayeredVectorChange(self):
        # test if a is docked with b is docked with c that:
        # changes to a's vector is the only actor_update that occurs
        self.fail("todo")

    def testDockedPlayerMovesRoomWithParent(self):
        # test of player is docked with B that:
        # when B moves room player moves as well and is restored docked
        self.fail("todo")

    def testParentNoLongerNEeded(self):
        self.fail("delete the parent field in actor")

    def testVisible(self):
        self.actor.visible = True
        self.assertEquals([], self.vision.messages)

        self.actor.visible = False
        self.assertEquals(("actor_becomes_invisible", self.actor),
            self.vision.messages[-1])

        self.actor.visible = True
        self.assertEquals(("actor_becomes_visible", self.actor),
            self.vision.messages[-1])

    def testDockingUpdates(self):
        self.actor2 = Actor(self.room, "mock_actor", Script("actor_script",
            ActorTest))

        self.actor2.dock_with(self.actor)

        self.assertEquals([
            ("actor_state_changed", self.actor2),
            ("actor_state_changed", self.actor),
            ],
            self.vision.messages)

        self.actor2.undock()

        self.assertEquals([
            ("actor_state_changed", self.actor2),
            ("actor_state_changed", self.actor),
            ("actor_vector_changed", self.actor2),
            ("actor_state_changed", self.actor),
            ("actor_state_changed", self.actor2),
            ],
            self.vision.messages)

    def testSetPositionToOutsideRoomCorrectsPosition(self):
        self.room.put_actor(self.actor)

        self.assertEquals(Position(0, 0), self.actor.position)

        self.actor.position = Position(-1, -1)

        self.assertEquals(Position(-1, -1), self.actor.position)

    def testCreateChildActor(self):
        self.actor.username = "bob"
        child = self.actor.create_actor("child", "actor_script")

        self.assertEquals(self.actor.position, child.position)
        self.assertEquals(self.actor, child.docked_with)
        self.assertFalse(child.visible)

        child = self.actor.create_actor("child", "actor_script", docked=False,
            position=Position(5, 5), visible=True)

        self.assertEquals(Position(5, 5), child.position)
        self.assertEquals(None, child.docked_with)
        self.assertTrue(child.visible)

        self.assertEquals(self.actor.actor_id, child.parent_id)
        self.assertEquals(None, self.actor.parent_id)
        self.assertEquals("bob", child.username)

    def testMoveUpdateGThread(self):
        self.actor.position = Position(10, 10)
        self.actor.move_to(Position(50, 10),
            [Position(10, 10), Position(25, 10), Position(50, 10)])

        MockTimer.fast_forward(3)
        self.assertEquals(Position(13, 10), self.actor.position)
        self.assertEquals(
            [Position(10, 10), Position(25, 10), Position(50, 10)],
            self.actor.path)
        self.assertEquals(Vector(Position(10, 10), 0, Position(25, 10), 15),
            self.actor.vector)

        MockTimer.fast_forward(17)
        self.assertEquals(Position(30, 10), self.actor.position)
        self.assertEquals(
            [Position(25, 10), Position(50, 10)],
            self.actor.path)
        self.assertEquals(Vector(Position(25, 10), 15, Position(50, 10), 40),
            self.actor.vector)

        MockTimer.fast_forward(15)
        self.assertEquals(Position(45, 10), self.actor.position)
        self.assertEquals(
            [Position(25, 10), Position(50, 10)],
            self.actor.path)
        self.assertEquals(Vector(Position(25, 10), 15, Position(50, 10), 40),
            self.actor.vector)

        MockTimer.fast_forward(10)
        self.assertEquals(Position(50, 10), self.actor.position)
        self.assertEquals(
            [Position(50, 10)],
            self.actor.path)
        self.assertEquals(Vector(Position(25, 10), 15, Position(50, 10), 40),
            self.actor.vector)

    def testTimeToVectorEnd(self):
        self.actor.move_to(Position(20, 10))
        self.assertEquals(22, round(self.actor.vector.time_to_destination()))

        self.actor.move_to(Position(30, 10),
            [Position(20, 10), Position(30, 10)])
        self.assertEquals(10, self.actor.vector.time_to_destination())

    def testTrackTargetVector(self):
        self.actor2 = Actor(self.room, "mock_actor", Script("actor_script",
            ActorTest))
        self.room.put_actor(self.actor2, Position(30, 10))

        def actor_script(actor):
            actors = actor.room.actors['id2']
            target = actors[0]
            actor.state.start_time = Timer.now()
            actor.track_vector(target, 30)
            actor.state.end_time = Timer.now()

        self.actor2.move_to(Position(50, 10))

        MockTimer.fast_forward(5)

    def testIfVectorOrPositionSetWhileMovingKillMoveGThread(self):
        pass

    def testRemove(self):
        self.actor2 = Actor(self.room, "mock_actor", Script("actor_script",
            ActorTest))
        self.room.put_actor(self.actor2, Position(30, 10))
        self.actor2.remove()

        self.assertTrue('id2' in
            self.node.container._remove_queue.queue)
#        self.assertEquals({'actors': {}, 'rooms': {}},
#            self.node.container.dbase.dbases)

    def testRemoveDocked(self):
        self.actor2 = Actor(self.room, "mock_actor", Script("actor_script",
            ActorTest))
        self.room.put_actor(self.actor2, Position(30, 10))
        child1 = self.actor2.create_actor("child1", "actor_script")

        self.actor2.remove()

        self.assertTrue('id2' in
            self.node.container._remove_queue.queue)
        self.assertTrue('id3' in
            self.node.container._remove_queue.queue)
#        self.assertEquals({'actors': {}, 'rooms': {}},
#            self.node.container.dbase.dbases)

    def testStateitems(self):
        self.actor.state.inner = {}
        self.actor.state.inner.something = {}
        self.actor.state.inner.something.value = "hello"

        self.assertEquals("hello",
            self.actor._get_state_val("inner.something.value".split('.')))

        self.assertEquals(None, self.actor._get_state_val(
            "inner.nope".split('.')))
        self.assertEquals(None, self.actor._get_state_val(
            "nope.nope".split('.')))
        self.assertEquals(None,
            self.actor._get_state_val(
                "inner.something.value.toofar".split('.')))

    def testSetStateItem(self):
        self.actor.state.inner = {}
        self.actor.state.inner.something = {}
        self.actor.state.inner.something.value = "hello"

        self.actor._set_state_val("inner.something.value".split('.'), "there")

        self.assertEquals("there", self.actor.state.inner.something.value)
