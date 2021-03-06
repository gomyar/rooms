
import unittest
from mock import patch
from mock import Mock

from rooms.room import Room
from rooms.room import Door
from rooms.room import Tag
from rooms.vision import Vision
from rooms.position import Position
from rooms.testutils import MockGeog
from rooms.testutils import MockNode
from rooms.testutils import MockActor
from rooms.testutils import MockContainer
from rooms.testutils import MockIDFactory
from rooms.testutils import MockDbase
from rooms.container import Container
from rooms.geography.basic_geography import BasicGeography
from rooms.player import PlayerActor
from rooms.script import Script
from rooms.testutils import MockVision
from rooms.actor import Actor
from rooms.node import Node
from rooms.room import RoomObject
from testutils import MockTimer


def created(actor):
    actor.state['created'] = True


class RoomTest(unittest.TestCase):
    def setUp(self):
        self.script = Script("room_test", RoomTest)
        self.dbase = MockDbase()
        self.container = Container(self.dbase, None)

        self.node = Node(self.container, 'alpha', '192.168.0.11')
        self.node.scripts['rooms.room_test'] = self.script
        self.container.node = self.node

        self.room = Room("game1", "room1", self.node)
        self.room.coords(0, 0, 50, 50)
        self.geography = MockGeog()
        self.room.geography = self.geography
        self.vision = MockVision()
        self.room.vision = self.vision
        MockIDFactory.setup_mock()
        MockTimer.setup_mock()

    def tearDown(self):
        MockIDFactory.teardown_mock()

    def testInitialSetup(self):
        self.assertEquals(50, self.room.width)
        self.assertEquals(50, self.room.height)
        self.assertEquals(Position(-25, -25, 0), self.room.topleft)
        self.assertEquals(Position(25, 25, 0), self.room.bottomright)
        self.assertEquals(Position(25, 25, 0), self.room.position)

    def testCreateActor(self):
        actor = self.room.create_actor("mock_actor", "rooms.room_test")
        self.assertTrue(actor.state.created)
        self.assertFalse(actor._script_gthread is None)
        self.assertEquals(created, actor.script.script_module.created)
        self.assertEquals(self.room, actor.room)
        self.assertEquals(actor, self.room.actors['id1'])
        self.assertEquals(None, actor.username)

        self.player = PlayerActor(self.room, "player", "rooms.room_test", "bob")
        actor2 = self.room.create_actor("mock_actor", "rooms.room_test",
            username=self.player.username)
        self.assertEquals("bob", actor2.username)

        actor = self.room.create_actor("mock_actor", "rooms.room_test",
            position=Position(10, 10))
        self.assertEquals(actor.position, Position(10, 10))

        actor = self.room.create_actor("invisible", "rooms.room_test",
            visible=False)
        self.assertFalse(actor.visible)

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
            [Position(10, 20), Position(25, 25)],
            self.room.find_path(Position(10, 20), Position(30, 40)))

    def testActorEnterDoor(self):
        self.door = Door("room2", Position(5, 5), Position(10, 10))
        self.actor = MockActor("actor1")
        self.room.put_actor(self.actor)

        self.room.doors.append(self.door)
        actor = self.room.create_actor("mock_actor", "rooms.room_test")

        self.room.actor_enters(actor, self.door)

        expected = [('actor_state_changed', actor),
            ('actor_removed', actor)]
        self.assertEquals(expected, self.vision.messages)

    def testActorAddRemove(self):
        newactor1 = MockActor("new1")
        self.room.put_actor(newactor1, Position(5, 5))

        self.assertEquals(1, len(self.room.actors))
        self.assertEquals("new1", self.room.actors.values()[0].actor_id)
        self.assertEquals(Position(5, 5), self.room.actors['new1'].vector.start_pos)
        self.assertEquals(Position(5, 5), self.room.actors['new1'].vector.end_pos)
        MockTimer.fast_forward(0)
        self.assertEquals([('kickoff', (newactor1,), {})],
            newactor1.script.called)

    def testSendRemoveUpdateOnRemoveActor(self):
        newactor1 = MockActor("new1")
        listener = MockActor("listener1")
        self.room.put_actor(newactor1, Position(5, 5))
        self.room.put_actor(listener, Position(1, 1))

        self.room._remove_actor(newactor1)

        self.assertEquals([("actor_removed", newactor1)], self.vision.messages)

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

        self.assertEquals(tag1, self.room.find_one_tag('tag'))

    def testFindObjects(self):
        object1 = RoomObject('test1', Position(0, 0))
        object1.info['key1'] = 'value1'

        object2 = RoomObject('test1', Position(0, 0))
        object2.info['key1'] = 'value2'

        self.room.room_objects.append(object1)
        self.room.room_objects.append(object2)

        found = self.room.find_room_objects('test1')
        self.assertEquals(2, len(found))
        self.assertTrue(object1 in found)
        self.assertTrue(object2 in found)

        self.assertEquals(object1, self.room.find_one_room_object('test1'))

    def testActorsAddedToRoomOutsideBoundariesArePositionedInside(self):
        newactor1 = MockActor("new1")
        self.room.put_actor(newactor1, Position(-5, -5))
        self.assertEquals(Position(-5, -5), newactor1.position)

        newactor2 = MockActor("new1")
        self.room.put_actor(newactor2, Position(55, 55))
        self.assertEquals(Position(25, 25), newactor2.position)

    def testFindPathCorrectPosition(self):
        path = self.room.find_path(Position(-1, -2), Position(3, 4))
        self.assertEquals([
            Position(-1, -2), Position(3, 4),
        ], path)
        path = self.room.find_path(Position(-60, -80), Position(3, 4))
        self.assertEquals([
            Position(-25, -25), Position(3, 4),
        ], path)

    def testSendMessage(self):
        self.vision = Vision(self.room)
        self.room.vision = self.vision

        actor = self.room.create_actor("test", "rooms.room_test")

        queue = self.room.vision.connect_vision_queue(actor.actor_id)

        command = queue.get_nowait()
        command = queue.get_nowait()
        self.assertTrue(queue.empty())

        self.room.send_message("test_message", actor.position,
            dict(key="value"))

        message = queue.get_nowait()

        self.assertEquals({'data': {'key': 'value'},
            'command': 'message',
            'message_type': 'test_message',
            'position': {u'x': 0.0, u'y': 0.0, u'z': 0.0}}
        , message)

    def testFindActors(self):
        actor1 = self.room.create_actor("test1", "rooms.room_test",
            state=dict(key="value1"))
        actor2 = self.room.create_actor("test1", "rooms.room_test",
            state=dict(key="value2"))
        actor3 = self.room.create_actor("test2", "rooms.room_test",
            state=dict(key="value1"))

        found = self.room.find_actors(actor_type="test1")
        self.assertEquals(set([actor1, actor2]), set(found))

        found = self.room.find_actors(actor_type="test2")
        self.assertEquals(set([actor3]), set(found))

        found = self.room.find_actors(state=dict(key="value1"))
        self.assertEquals(set([actor1, actor3]), set(found))

        found = self.room.find_actors(actor_type="test1",
            state=dict(key="value1"))
        self.assertEquals(set([actor1]), set(found))

    def testRemoveChildActors(self):
        self.assertEquals(0, len(self.room.actors))
        actor1 = self.room.create_actor("test1", "rooms.room_test")
        child1 = actor1.create_actor("child1", "rooms.room_test")
        child2 = child1.create_actor("child2", "rooms.room_test")

        self.assertEquals(3, len(self.room.actors))

        removed = self.room._remove_docked(actor1)

        self.assertEquals([actor1], self.room.actors.values())
        self.assertEquals([child1, child2], removed)

    @patch("gevent.spawn")
    def testStartStopRoomLoaderActors(self, spawn):
        # make sure start starts all the actors
        # and the actorloader
        mock_actor = MockActor('actor1')
        mock_actor.kick = Mock()
        self.room.actors['actor1'] = mock_actor
        self.room.start()

        self.assertEquals(self.room.actor_loader.load_loop,
                          spawn.call_args_list[0][0][0])
        self.assertTrue(mock_actor.kick.called)

    def testSendRoomEvent(self):
        ''' Send an event through the vision queue to all actor queues in the room
        '''
