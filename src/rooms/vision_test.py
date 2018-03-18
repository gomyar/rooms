
import unittest

from rooms.room import Room
from rooms.position import Position
from rooms.vector import build_vector
from rooms.actor import Actor
from rooms.vision import Vision


class SimpleVisionTest(unittest.TestCase):
    def setUp(self):
        self.room = Room("game1", "map1.room1", None)
        self.room.coords(0, 0, 100, 100)
        self.vision = Vision(self.room)
        self.room.vision = self.vision

        self.actor1 = Actor(None, None, None, actor_id="actor1")
        self.actor1.vector = build_vector(1, 1, 5, 5)
        self.actor2 = Actor(None, None, None, actor_id="actor2")
        self.actor2.vector = build_vector(1, 1, 5, 5)

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

        self.actor1.send_event({'type': 'random'})

        self.assertEquals(
            {'command': 'actor_event', 'actor_id': self.actor1.actor_id,
             'data': {'type': 'random'}}, queue1.get_nowait())
        self.assertEquals(
            {'command': 'actor_event', 'actor_id': self.actor1.actor_id,
             'data': {'type': 'random'}}, queue2.get_nowait())

        # invisible actors tell no tales
        self.actor1.visible = False
        # clear out invisible events
        queue1.queue.clear()
        queue2.queue.clear()

        self.actor1.send_event({'type': 'second'})

        self.assertEquals(
            {'command': 'actor_event', 'actor_id': self.actor1.actor_id,
             'data': {'type': 'second'}}, queue1.get_nowait())
        self.assertTrue(queue2.empty())

        # also docked actors

        # also admin queues
