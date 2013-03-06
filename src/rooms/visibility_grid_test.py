
import unittest

from rooms.room import Room
from rooms.visibility_grid import VisibilityGrid


class MockActor(object):
    def __init__(self, name, x, y, vision_distance=0):
        self.name = name
        self.updates = []
        self.pos = x, y
        self.vision_distance = vision_distance

    def __repr__(self):
        return "<MockActor %s>" % (self.name,)

    def position(self):
        return self.pos

    def actor_added(self, actor):
        self.updates.append(("added", actor))

    def actor_removed(self, actor):
        self.updates.append(("removed", actor))

    def actor_updated(self, actor):
        self.updates.append(("updated", actor))


class VisibilityGridTest(unittest.TestCase):
    def setUp(self):
        self.visibility_grid = VisibilityGrid(50, 50, 10)

        self.actor1 = MockActor("actor1", 25, 25, 10)
        self.actor2 = MockActor("actor2", 15, 15, 0)

    def testGridPoints(self):
        self.assertEquals([(1, 1), (2, 1), (3, 1),
            (1, 2), (2, 2), (3, 2),
            (1, 3), (2, 3), (3, 3)],
            list(self.visibility_grid._gridpoints(25, 25, 10)))
        self.assertEquals([(1, 1), (2, 1), (3, 1),
            (1, 2), (2, 2), (3, 2),
            (1, 3), (2, 3), (3, 3)],
            list(self.visibility_grid._gridpoints(29, 29, 10)))
        self.assertEquals([(1, 1), (2, 1), (3, 1),
            (1, 2), (2, 2), (3, 2),
            (1, 3), (2, 3), (3, 3)],
            list(self.visibility_grid._gridpoints(21, 21, 10)))

        self.assertEquals([(3, 3), (4, 3), (3, 4), (4, 4)],
            list(self.visibility_grid._gridpoints(41, 41, 10)))

    def testMovement(self):
        # actor1 enters room.
        self.visibility_grid._register_listener(self.actor1)
        # actor1 registers interest in x sectors
        # actor1 get responses for each sector, one at a time []
        self.assertEquals([], self.actor1.updates)

        # actor2 enters room
        self.visibility_grid.add_actor(self.actor2)
        # actor2 registers
        # actor2 not listener and gets no responses
        self.assertEquals([], self.actor2.updates)
        # actor1 gets response [actor2]
        self.assertEquals([("added", self.actor2)], self.actor1.updates)

        # actor2 moves away slightly
        self.actor2.pos = 5, 5
        self.visibility_grid.update_actor_position(self.actor2)

        # actor1 gets removal message
        self.assertEquals([("added", self.actor2), ("removed", self.actor2)],
            self.actor1.updates)
        # actor2 gets nothing
        self.assertEquals([], self.actor2.updates)

    def testListenerMovesOutOfRange(self):
        # actor1 enters room.
        self.visibility_grid._register_listener(self.actor1)

        # actor2 enters room
        self.visibility_grid.add_actor(self.actor2)
        # actor1 gets add message [actor2]
        self.assertEquals([("added", self.actor2)], self.actor1.updates)

        # actor1 moves out of range
        self.actor1.pos = 35, 35
        self.visibility_grid.update_actor_position(self.actor1)
        # actor1 gets removal message [actor2]
        self.assertEquals([("added", self.actor2), ("removed", self.actor2)],
            self.actor1.updates)
        # actor2 gets no removal message
        self.assertEquals([],
            self.actor2.updates)

    def testTwoListeners(self):
        self.actor2.vision_distance = 10

        # actor1 enters room.
        self.visibility_grid._register_listener(self.actor1)
        # actor2 registers
        self.visibility_grid._register_listener(self.actor2)

        # actor2 gets add message
        self.assertEquals([("added", self.actor1)], self.actor2.updates)
        # actor1 gets add message
        self.assertEquals([("added", self.actor2)], self.actor1.updates)

        # actor2 moves away slightly
        self.actor2.pos = 5, 5
        self.visibility_grid.update_actor_position(self.actor2)

        # actor1 gets removal message
        self.assertEquals([("added", self.actor2), ("removed", self.actor2)],
            self.actor1.updates)
        # actor2 gets nothing
        self.assertEquals([("added", self.actor1), ("removed", self.actor1)],
            self.actor2.updates)

    def testTwoListenersOneActor(self):
        self.actor2.vision_distance = 10

        self.actor3 = MockActor("actor3", 15, 15, 0)

        # actor1 enters room.
        self.visibility_grid._register_listener(self.actor1)
        # actor2 registers
        self.visibility_grid._register_listener(self.actor2)
        # actor 3 added
        self.visibility_grid._add_actor(self.actor3)

        # actor2 gets add message
        self.assertEquals([("added", self.actor1), ("added", self.actor3)],
            self.actor2.updates)
        # actor1 gets add message
        self.assertEquals([("added", self.actor2), ("added", self.actor3)],
            self.actor1.updates)
        # nothing for actor3
        self.assertEquals([], self.actor3.updates)

        # actor2 moves away slightly
        self.actor2.pos = 5, 5
        self.visibility_grid.update_actor_position(self.actor2)

        # actor1 gets removal message
        self.assertEquals([("added", self.actor2), ("added", self.actor3),
            ("removed", self.actor2)],
            self.actor1.updates)
        # actor2 gets nothing
        self.assertEquals([("added", self.actor1), ("added", self.actor3),
            ("removed", self.actor1)],
            self.actor2.updates)
        # nothing for actor3
        self.assertEquals([], self.actor3.updates)


