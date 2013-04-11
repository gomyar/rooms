
import unittest

from rooms.room import Room
from rooms.visibility_grid import VisibilityGrid


class MockActor(object):
    def __init__(self, name, x, y, vision_distance=0, visible_to_all=False):
        self.name = name
        self.updates = []
        self.pos = x, y
        self.vision_distance = vision_distance
        self.visible_to_all = visible_to_all

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

    def _update(self, update_id, **kwargs):
        self.updates.append((update_id, kwargs))


class VisibilityGridTest(unittest.TestCase):
    def setUp(self):
        self.visibility_grid = VisibilityGrid(1000, 1000, 10)

        self.actor1 = MockActor("actor1", 25, 25, 10)
        self.actor2 = MockActor("actor2", 15, 15, 0)

    def testGridPoints(self):
        self.visibility_grid = VisibilityGrid(50, 50, 10)

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
        self.visibility_grid.register_listener(self.actor1)
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
        self.visibility_grid.register_listener(self.actor1)
        self.visibility_grid.add_actor(self.actor1)

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
        self.visibility_grid.register_listener(self.actor1)
        self.visibility_grid.add_actor(self.actor1)
        # actor2 registers
        self.visibility_grid.register_listener(self.actor2)
        self.visibility_grid.add_actor(self.actor2)

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
        self.visibility_grid.register_listener(self.actor1)
        self.visibility_grid.add_actor(self.actor1)
        # actor2 registers
        self.visibility_grid.register_listener(self.actor2)
        self.visibility_grid.add_actor(self.actor2)
        # actor 3 added
        self.visibility_grid.add_actor(self.actor3)

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
        self.assertEquals([("added", self.actor2),
            ("added", self.actor3), ("removed", self.actor2)],
            self.actor1.updates)
        # actor2 gets nothing
        self.assertEquals([("added", self.actor1),
            ("added", self.actor3), ("removed", self.actor1)],
            self.actor2.updates)
        # nothing for actor3
        self.assertEquals([], self.actor3.updates)

    def testRegisteredGidsMovesWitActor(self):
        # actor1 enters room.
        self.visibility_grid.register_listener(self.actor1)
        self.visibility_grid.add_actor(self.actor1)

        self.assertEquals(set([(1, 2), (3, 2), (1, 3), (3, 3), (3, 1), (2, 1), (2, 3), (2, 2), (1, 1)]), self.visibility_grid.registered_gridpoints[self.actor1])
        self.assertEquals(set([(2, 2)]), self.visibility_grid._actor_sectors(self.actor1))

        self.actor1.pos = (35, 35)
        self.visibility_grid.update_actor_position(self.actor1)

        self.assertEquals(set([(3, 2), (3, 3), (4, 4), (2, 3), (4, 3), (2, 2), (4, 2), (3, 4), (2, 4)]), self.visibility_grid.registered_gridpoints[self.actor1])
        self.assertEquals(set([(3, 3)]), self.visibility_grid._actor_sectors(self.actor1))

    def testGridRealExample(self):
        actor = MockActor("actor1", 131, 131, 500)

        self.assertEquals(4096, len(self.visibility_grid._gridpoints(131, 131, 500)))
        self.visibility_grid.register_listener(actor)
        self.assertEquals(4096, len(self.visibility_grid.registered_gridpoints[actor]))

    def testUpdateVisionDistance(self):
        actor1 = MockActor("actor1", 25, 25, 0)
        actor2 = MockActor("actor2", 15, 15, 0)

        self.visibility_grid.add_actor(actor1)
        self.visibility_grid.add_actor(actor2)

        self.assertEquals([], actor1.updates)
        self.assertEquals([], actor2.updates)

        actor1.vision_distance = 10
        self.visibility_grid.vision_distance_changed(actor1)

        # Note: self is not added. I like this.
        # nuh uh: self should be added (for player callback)
        self.assertEquals([("added", actor2)], actor1.updates)
        self.assertEquals([], actor2.updates)

        actor1.vision_distance = 0
        self.visibility_grid.vision_distance_changed(actor1)

        # Note: self is not added. I like this.
        self.assertEquals([("added", actor2), ("removed", actor2)],
            actor1.updates)
        self.assertEquals([], actor2.updates)

    def testRegisterListenerDoesntSendUpdate(self):
        actor1 = MockActor("actor1", 25, 25, 10)
        actor2 = MockActor("actor2", 15, 15, 10)

        self.visibility_grid.register_listener(actor1)
        self.visibility_grid.register_listener(actor2)

        self.assertEquals([], actor1.updates)
        self.assertEquals([], actor2.updates)

    def testActorVisibleToAll(self):
        actor1 = MockActor("actor1", 35, 35)
        actor2 = MockActor("actor2", 5, 5, 0, visible_to_all=True)

        self.visibility_grid.register_listener(actor1)
        self.visibility_grid.add_actor(actor2)

        self.assertEquals([("added", actor2)], actor1.updates)

        self.visibility_grid.send_update_actor(actor2)
        self.assertEquals([("added", actor2), ("updated", actor2)],
            actor1.updates)

        self.visibility_grid.send_update_event(actor2, "blah")
        self.assertEquals([("added", actor2), ("updated", actor2),
            ("blah", {})],
            actor1.updates)

        self.visibility_grid.remove_actor(actor2)

        self.assertEquals([("added", actor2), ("updated", actor2),
            ("blah", {}), ("removed", actor2)],
            actor1.updates)

    def testVisibleToAllMovesOutsideRange(self):
        self.actor2 = MockActor("actor2", 15, 15, 0, visible_to_all=True)
        # actor1 enters room.
        self.visibility_grid.register_listener(self.actor1)

        # actor2 enters room
        self.visibility_grid.add_actor(self.actor2)
        # actor1 gets response [actor2]
        self.assertEquals([("added", self.actor2)], self.actor1.updates)

        # actor2 moves away slightly
        self.actor2.pos = 5, 5
        self.visibility_grid.update_actor_position(self.actor2)

        # actor1 gets no removal message from visible_to_all actor
        self.assertEquals([("added", self.actor2)],
            self.actor1.updates)

        self.actor1.pos = 35, 35
        self.visibility_grid.update_actor_position(self.actor1)

        self.assertEquals([("added", self.actor2)],
            self.actor1.updates)

    def testAddRegisteredListenerAfterVisibleToAll(self):
        self.actor2 = MockActor("actor2", 15, 15, 0, visible_to_all=True)

        # actor2 enters room
        self.visibility_grid.add_actor(self.actor2)
        # actor1 enters room.
        self.visibility_grid.register_listener(self.actor1)
        # actor1 gets response [actor2]
        self.assertEquals([("added", self.actor2)], self.actor1.updates)

        # actor2 moves away slightly
        self.actor2.pos = 5, 5
        self.visibility_grid.update_actor_position(self.actor2)

        # actor1 gets no removal message from visible_to_all actor
        self.assertEquals([("added", self.actor2)],
            self.actor1.updates)

        self.actor1.pos = 35, 35
        self.visibility_grid.update_actor_position(self.actor1)

        self.assertEquals([("added", self.actor2)],
            self.actor1.updates)

    def testRemoveRegisteredListenerAfterVisibleToAll(self):
        self.actor2 = MockActor("actor2", 15, 15, 0, visible_to_all=True)

        # actor2 enters room
        self.visibility_grid.add_actor(self.actor2)
        # actor1 enters room.
        self.visibility_grid.register_listener(self.actor1)
        # actor1 gets response [actor2]
        self.assertEquals([("added", self.actor2)], self.actor1.updates)

        self.visibility_grid.unregister_listener(self.actor1)

        self.assertEquals([("added", self.actor2), ("removed", self.actor2)],
            self.actor1.updates)

    def testJustMakingSureRemovingVisibletoAllWorks(self):
        self.actor2 = MockActor("actor2", 15, 15, 0, visible_to_all=True)

        # actor2 enters room
        self.visibility_grid.add_actor(self.actor2)
        # actor1 enters room.
        self.visibility_grid.register_listener(self.actor1)
        # actor1 gets response [actor2]
        self.assertEquals([("added", self.actor2)], self.actor1.updates)

        self.visibility_grid.remove_actor(self.actor2)

        self.assertEquals([("added", self.actor2), ("removed", self.actor2)],
            self.actor1.updates)
