
import unittest

from rooms.vector import create_vector, Vector
from rooms.visibility import Visibility
from rooms.testutils import MockActor
from rooms.position import Position


class MockListener(object):
    def __init__(self, actor):
        self.messages = []
        self.actor = actor

    def actor_update(self, actor):
        self.messages.append(("actor_update", actor))

    def actor_removed(self, actor):
        self.messages.append(("actor_removed", actor))

    def actor_state_changed(self, actor):
        self.messages.append(("actor_state_changed", actor))

    def actor_vector_changed(self, actor, previous_vector):
        self.messages.append(("actor_vector_changed", actor, previous_vector))

    def actor_becomes_visible(self, actor):
        self.messages.append(("actor_becomes_visible", actor))

    def actor_becomes_invisible(self, actor):
        self.messages.append(("actor_becomes_invisible", actor))


class VisibilityTest(unittest.TestCase):
    def setUp(self):
        self.visibility = Visibility()
        self.actor = MockActor("actor1")
        self.actor.vector = Vector(Position(0, 0), 0, Position(10, 0), 10)
        self.actor2 = MockActor("actor2")
        self.actor2.vector = Vector(Position(0, 0), 0, Position(10, 0), 10)
        self.connection = MockListener(self.actor)

    def testBasicListen(self):
        self.visibility.add_visible_area(Position(0, 0), Position(10, 10))
        self.visibility.add_listener(self.connection)

        self.visibility.actor_update(self.actor2)
        self.assertEquals([("actor_update", self.actor2)],
            self.connection.messages)

        self.visibility.actor_update(self.actor2)
        self.assertEquals(("actor_update", self.actor2),
            self.connection.messages[-1])

        self.visibility.actor_removed(self.actor2)
        self.assertEquals(("actor_removed", self.actor2),
            self.connection.messages[-1])

        self.visibility.actor_state_changed(self.actor2)
        self.assertEquals(("actor_state_changed", self.actor2),
            self.connection.messages[-1])

        previous_vector = Vector(Position(0, 0), 0, Position(10, 10), 15)
        self.visibility.actor_vector_changed(self.actor2, previous_vector)
        self.assertEquals(
            ("actor_vector_changed", self.actor2, previous_vector),
            self.connection.messages[-1])

        self.visibility.actor_becomes_visible(self.actor2)
        self.assertEquals(("actor_becomes_visible", self.actor2),
            self.connection.messages[-1])

        self.visibility.actor_becomes_invisible(self.actor2)
        self.assertEquals(("actor_becomes_invisible", self.actor2),
            self.connection.messages[-1])

    def testVisibleArea(self):
        self.actor.vector = Vector(Position(0, 0), 0, Position(2, 0), 10)
        self.actor2.vector = Vector(Position(8, 0), 0, Position(10, 0), 10)

        self.visibility.add_visible_area(Position(0, 0), Position(5, 5))
        self.visibility.add_listener(self.connection)
        self.visibility.actor_update(self.actor2)

        self.assertEquals([], self.connection.messages)

    def testChangeVectorSendsActorUpdates(self):
        # listening to right hand area
        self.actor.vector = Vector(Position(6, 0), 0, Position(10, 0), 10)

        # two visible areas
        self.visibility.add_visible_area(Position(0, 0), Position(5, 5))
        self.visibility.add_visible_area(Position(5, 0), Position(10, 5))
        self.visibility.add_listener(self.connection)

        # move from one area to the next
        self.actor2.vector = Vector(Position(0, 0), 0, Position(6, 0), 10)
        previous_vector = Vector(Position(0, 0), 0, Position(2, 0), 10)

        self.visibility.actor_vector_changed(self.actor2, previous_vector)

        self.assertEquals([
            ("actor_vector_changed", self.actor2, previous_vector)],
            self.connection.messages)

    def testChangeVectorOutOfVisibleArea(self):
        # listening to right hand area
        self.actor.vector = Vector(Position(6, 0), 0, Position(10, 0), 10)

        # two visible areas
        self.visibility.add_visible_area(Position(0, 0), Position(5, 5))
        self.visibility.add_visible_area(Position(5, 0), Position(10, 5))
        self.visibility.add_listener(self.connection)

        # move from one area to the next
        self.actor2.vector = Vector(Position(0, 0), 0, Position(2, 0), 10)
        previous_vector = Vector(Position(0, 0), 0, Position(6, 0), 10)

        self.visibility.actor_vector_changed(self.actor2, previous_vector)

        self.assertEquals([
            ("actor_removed", self.actor2)],
            self.connection.messages)
