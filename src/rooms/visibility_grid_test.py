
import unittest

from rooms.room import Room
from rooms.visibility_grid import VisibilityGrid


class MockActor(object):
    def __init__(self, name):
        self.name = name
        self.updates = []

    def __repr__(self):
        return "<MockActor %s>" % (self.name,)

    def actor_added(self, actor):
        self.updates.append(("added", actor))

    def actor_removed(self, actor):
        self.updates.append(("removed", actor))

    def actor_updated(self, actor):
        self.updates.append(("updated", actor))


class VisibilityGridTest(unittest.TestCase):
    def setUp(self):
        self.visibility_grid = VisibilityGrid(50, 50, 10)

        self.actor1 = MockActor("actor1")
        self.actor2 = MockActor("actor2")

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

    def testActorRemoved(self):
        self.visibility_grid.add_actor(self.actor1, 25, 25, 10)
        self.visibility_grid.remove_actor(self.actor1)

        self.visibility_grid.add_actor(self.actor2, 15, 15, 10)
        self.assertEquals([], self.actor1.updates)

    def testMovement(self):
        # actor1 enters room.
        self.visibility_grid.add_actor(self.actor1, 25, 25, 10)
        # actor1 registers interest in x sectors
        # actor1 get responses for each sector, one at a time []
        self.assertEquals([], self.actor1.updates)

        # actor2 enters room
        self.visibility_grid.add_actor(self.actor2, 15, 15, 10)
        # actor2 registers
        # actor2 get responses [actor1]
        self.assertEquals([("added", self.actor1)], self.actor2.updates)
        # actor1 gets response [actor2]
        self.assertEquals([("added", self.actor2)], self.actor1.updates)

        # actor2 moves away slightly
        self.visibility_grid.update_actor(self.actor2, 5, 5, 10)

        # actor1 gets no removal message as intersection still exists
        self.assertEquals([("added", self.actor2)], self.actor1.updates)
        # actor2 gets no removal message
        self.assertEquals([("added", self.actor1)], self.actor2.updates)

        # actor1 moves out of range
        self.visibility_grid.update_actor(self.actor1, 35, 35, 10)
        # actor1 gets removal message [actor2]
        self.assertEquals([("added", self.actor2), ("removed", self.actor2)],
            self.actor1.updates)
        # actor2 gets removal message [actor1]
        self.assertEquals([("added", self.actor1), ("removed", self.actor1)],
            self.actor2.updates)
