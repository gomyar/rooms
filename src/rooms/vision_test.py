
import unittest

from rooms.room import Room
from rooms.position import Position
from rooms.vector import build_vector
from rooms.actor import Actor
from rooms.vision import Vision
from rooms.geography.basic_geography import BasicGeography


class SimpleVisionTest(unittest.TestCase):
    def setUp(self):
        self.room = Room("game1", "map1.room1", None)
        self.room.coords(0, 0, 100, 100)
        self.vision = Vision(self.room)
        self.room.vision = self.vision
        self.room.geography = BasicGeography()

        self.actor1 = Actor(self.room, None, None, actor_id="actor1")
        self.actor1.position = Position(1, 1)
        self.actor1.move_to(Position(5, 5))
        self.actor2 = Actor(self.room, None, None, actor_id="actor2")
        self.actor2.position = Position(1, 1)
        self.actor2.move_to(Position(5, 5))

    def testPropagateMessages(self):
        self.room.put_actor(self.actor1)

        queue = self.room.vision.connect_vision_queue(self.actor1.actor_id)

        command = queue.get_nowait()
        self.assertEquals("sync", command['command'])
        command = queue.get_nowait()
        self.assertEquals("actor_update", command['command'])
        self.assertTrue(queue.empty())

        self.actor1.state.something = "else"

        command = queue.get_nowait()
        self.assertEquals("actor_update", command['command'])
        self.assertTrue(queue.empty())

        self.actor1.visible = False

        command = queue.get_nowait()
        self.assertEquals("actor_update", command['command'])
        self.assertTrue(queue.empty())

    def testRemoveActor(self):
        self.room.put_actor(self.actor1)
        self.room.put_actor(self.actor2)

        queue = self.room.vision.connect_vision_queue(self.actor1.actor_id)

        command = queue.get_nowait()
        self.assertEquals("sync", command['command'])
        command = queue.get_nowait()
        self.assertEquals("actor_update", command['command'])
        command = queue.get_nowait()
        self.assertEquals("actor_update", command['command'])
        self.assertTrue(queue.empty())

        self.room._remove_actor(self.actor2)

        command = queue.get_nowait()
        self.assertEquals("remove_actor", command['command'])
        self.assertTrue(queue.empty())


    def testActorInvisible(self):
        self.room.put_actor(self.actor1)
        self.room.put_actor(self.actor2)

        queue = self.room.vision.connect_vision_queue(self.actor1.actor_id)

        command = queue.get_nowait()
        self.assertEquals("sync", command['command'])
        command = queue.get_nowait()
        self.assertEquals("actor_update", command['command'])
        command = queue.get_nowait()
        self.assertEquals("actor_update", command['command'])
        self.assertTrue(queue.empty())

        self.actor2.visible = False

        command = queue.get_nowait()
        self.assertEquals("remove_actor", command['command'])
        self.assertTrue(queue.empty())

    def testMultiLayeredDockingVisibility(self):
        # test if a is docked with b is docked with c that:
        # c is visible to all
        # b is invisible to all, but visible to a
        # a is invisible to all, but visible to a
        pass

    def testSendActorEvent(self):
        self.room.put_actor(self.actor1)
        self.room.put_actor(self.actor2)

        queue1 = self.room.vision.connect_vision_queue(self.actor1.actor_id)
        queue2 = self.room.vision.connect_vision_queue(self.actor2.actor_id)

        # clear out sync events
        queue1.queue.clear()
        queue2.queue.clear()

        self.actor1.send_message({'type': 'random'})

        self.assertEquals(
            {'command': 'actor_message', 'actor_id': self.actor1.actor_id,
             'data': {'type': 'random'}}, queue1.get_nowait())
        self.assertEquals(
            {'command': 'actor_message', 'actor_id': self.actor1.actor_id,
             'data': {'type': 'random'}}, queue2.get_nowait())

        # invisible actors tell no tales
        self.actor1.visible = False
        # clear out invisible events
        queue1.queue.clear()
        queue2.queue.clear()

        self.actor1.send_message({'type': 'second'})

        self.assertEquals(
            {'command': 'actor_message', 'actor_id': self.actor1.actor_id,
             'data': {'type': 'second'}}, queue1.get_nowait())
        self.assertTrue(queue2.empty())

        # also docked actors

        # also admin queues

    def testSendRoomEvent(self):
        self.room.put_actor(self.actor1)
        self.room.put_actor(self.actor2)

        queue1 = self.room.vision.connect_vision_queue(self.actor1.actor_id)
        queue2 = self.room.vision.connect_vision_queue(self.actor2.actor_id)

        # clear out sync events
        queue1.queue.clear()
        queue2.queue.clear()

        self.room.send_message('test', Position(0, 0), {'type': 'random'})

        self.assertEquals(
            {'command': 'message',
            'data': {'type': 'random'},
            'message_type': 'test',
            'position': {u'x': 0.0, u'y': 0.0, u'z': 0.0}},
            queue1.get_nowait())
        self.assertEquals(
            {'command': 'message',
            'data': {'type': 'random'},
            'message_type': 'test',
            'position': {u'x': 0.0, u'y': 0.0, u'z': 0.0}},
            queue2.get_nowait())

        # also admin queues
