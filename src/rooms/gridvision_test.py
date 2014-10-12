
import unittest

from rooms.testutils import MockRoom
from rooms.position import Position
from rooms.vector import build_vector
from rooms.vector import Vector
from rooms.gridvision import GridVision
from rooms.gridvision import Area
from rooms.testutils import MockActor


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

    def actor_becomes_invisible(self, actor):
        self.messages.append(("actor_becomes_invisible", actor))

    def actor_becomes_visible(self, actor):
        self.messages.append(("actor_becomes_visible", actor))


class GridVisionTest(unittest.TestCase):
    def setUp(self):
        self.room = MockRoom("game1", "map1.roomq")
        self.room.topleft = Position(0, 0)
        self.room.bottomright = Position(100, 100)
        self.vision = GridVision(self.room, 10)
        self.actor1 = MockActor("actor1")
        self.actor1.vector = build_vector(1, 1, 5, 5)
        self.lactor = MockActor("listener1")
        self.lactor.vector = build_vector(11, 11, 15, 15)

    def testAreaLayout(self):
        # basic grid, 10 x 10
        self.assertEquals(100, len(self.vision.areas))
        self.assertEquals(Area(0, 0), self.vision.area_at(Position(2, 3)))
        self.assertEquals(None, self.vision.area_at(Position(-1, -1)))
        self.assertEquals(Area(9, 9), self.vision.area_at(Position(90, 90)))

    def testAreasAttachedToVisibleAreas(self):
        area = self.vision.area_at(Position(12, 13))
        self.assertEquals(9, len(area.linked))
        self.assertTrue(Area(0, 0) in list(area.linked))
        self.assertTrue(Area(2, 2) in list(area.linked))

    def testListenersAttachToSingleArea(self):
        listener = MockListener(self.lactor)
        self.vision.add_listener(listener)
        self.vision.actor_update(self.actor1)
        self.assertEquals([("actor_update", self.actor1)], listener.messages)
        self.assertEquals(self.vision.area_for_actor(self.actor1),
            self.vision.area_at(self.actor1.vector.start_pos))

        self.vision.actor_removed(self.actor1)
        self.assertEquals([
            ("actor_update", self.actor1),
            ("actor_removed", self.actor1),
            ], listener.messages)

    def testAllActorsAreKeptAsReferences(self):
        self.vision.actor_update(self.actor1)
        self.assertEquals(set([self.actor1]),
            self.vision.area_at(self.actor1.position).actors)

        self.vision.actor_removed(self.actor1)
        self.assertEquals(set([]),
            self.vision.area_at(self.actor1.position).actors)

    def testEventsPropagatedToAreaListeners(self):
        listener = MockListener(self.lactor)
        self.vision.add_listener(listener)

        self.vision.actor_update(self.actor1)
        self.assertEquals(("actor_update", self.actor1),
            listener.messages[-1])

        self.vision.actor_removed(self.actor1)
        self.assertEquals(("actor_removed", self.actor1),
            listener.messages[-1])

        previous = Vector(Position(2, 2), 0, Position(4, 4), 1)
        self.vision.actor_vector_changed(self.actor1, previous)
        self.assertEquals(("actor_vector_changed", self.actor1, previous),
            listener.messages[-1])

        self.vision.actor_state_changed(self.actor1)
        self.assertEquals(("actor_state_changed", self.actor1),
            listener.messages[-1])

        self.vision.actor_becomes_invisible(self.actor1)
        self.assertEquals(("actor_becomes_invisible", self.actor1),
            listener.messages[-1])

        self.vision.actor_becomes_visible(self.actor1)
        self.assertEquals(("actor_becomes_visible", self.actor1),
            listener.messages[-1])

    def testEveryPartOfTheRoomShouldBeCoveredByAVisionArea(self):
        self.assertEquals(Area(0, 0), self.vision.area_at(Position(0, 0)))
        self.assertEquals(Area(9, 9), self.vision.area_at(Position(99, 99)))
        self.assertEquals(None, self.vision.area_at(Position(100, 100)))

    def testActorMovesOutOfVisionArea(self):
        self.vision = GridVision(self.room, 10)
        self.actor1 = MockActor("actor1")
        previous = build_vector(21, 21, 25, 25)
        self.actor1.vector = previous
        self.lactor = MockActor("listener1")
        self.lactor.vector = build_vector(11, 11, 15, 15)

        # add actor and listener
        self.vision.actor_update(self.actor1)
        listener = MockListener(self.lactor)
        self.vision.add_listener(listener)

        # change vector to area outside vision distance
        self.actor1.vector = build_vector(35, 35, 45, 45)
        self.vision.actor_vector_changed(self.actor1, previous)

        self.assertEquals([
            ("actor_removed", self.actor1)
        ], listener.messages)

    def testActorMovesIntoVisionArea(self):
        self.vision = GridVision(self.room, 10)
        self.actor1 = MockActor("actor1")
        previous = build_vector(35, 35, 45, 45)
        self.actor1.vector = previous
        self.lactor = MockActor("listener1")
        self.lactor.vector = build_vector(11, 11, 15, 15)

        # add actor and listener
        self.vision.actor_update(self.actor1)
        listener = MockListener(self.lactor)
        self.vision.add_listener(listener)

        # change vector to area outside vision distance
        self.actor1.vector = build_vector(21, 21, 25, 25)
        self.vision.actor_vector_changed(self.actor1, previous)

        self.assertEquals([
            ("actor_update", self.actor1)
        ], listener.messages)

    def testActorMovesInNonVisibleAreas(self):
        self.vision = GridVision(self.room, 10)
        self.actor1 = MockActor("actor1")
        previous = build_vector(35, 35, 45, 45)
        self.actor1.vector = previous
        self.lactor = MockActor("listener1")
        self.lactor.vector = build_vector(11, 11, 15, 15)

        # add actor and listener
        self.vision.actor_update(self.actor1)
        listener = MockListener(self.lactor)
        self.vision.add_listener(listener)

        # change vector to area outside vision distance
        self.actor1.vector = build_vector(45, 45, 55, 55)
        self.vision.actor_vector_changed(self.actor1, previous)

        self.assertEquals([], listener.messages)
