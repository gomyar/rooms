
import unittest

from rooms.testutils import MockRoom
from rooms.testutils import MockActor
from rooms.actor import Actor
from rooms.player_connection import PlayerConnection


class PlayerConnectionTest(unittest.TestCase):
    def setUp(self):
        self.room = MockRoom("game1", "room1")
        self.actor = Actor(self.room, "test", None)
        self.actor.room = self.room
        self.actor2 = Actor(self.room, "test", None)
        self.actor2.room = self.room
        self.conn = PlayerConnection("game1", "bob", self.room, self.actor,
            "TOKEN1")

    def testConnection(self):
        queue = self.conn.new_queue()

        self.conn.actor_update(self.actor2)
        self.assertEquals('actor_update', queue.get()['command'])

        self.conn.actor_removed(self.actor2)
        self.assertEquals('remove_actor', queue.get()['command'])

        self.conn.actor_becomes_visible(self.actor2)
        self.assertEquals('actor_update', queue.get()['command'])

        self.conn.actor_becomes_invisible(self.actor2)
        self.assertEquals('remove_actor', queue.get()['command'])

    def testVisibility(self):
        queue = self.conn.new_queue()

        self.actor2.visible = False

        self.conn.actor_update(self.actor2)
        self.assertTrue(queue.empty())

        self.conn.actor_becomes_visible(self.actor2)
        self.assertTrue(queue.empty())

        self.conn.actor_becomes_invisible(self.actor2)
        self.assertTrue(queue.empty())

        self.actor2.visible = True

        self.conn.actor_update(self.actor2)
        self.assertEquals('actor_update', queue.get()['command'])

        self.conn.actor_becomes_visible(self.actor2)
        self.assertEquals('actor_update', queue.get()['command'])

        self.conn.actor_becomes_invisible(self.actor2)
        self.assertEquals('remove_actor', queue.get()['command'])
