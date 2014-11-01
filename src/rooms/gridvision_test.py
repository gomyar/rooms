
import unittest

from rooms.testutils import MockRoom
from rooms.position import Position
from rooms.vector import build_vector
from rooms.vector import Vector
from rooms.gridvision import GridVision
from rooms.gridvision import Area
from rooms.testutils import MockActor
from rooms.testutils import MockPlayerConnection


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

        self.vision.add_actor(self.actor1)
        self.vision.add_actor(self.lactor)

    def testAreaLayout(self):
        # basic grid, 10 x 10
        self.assertEquals(121, len(self.vision.areas))
        self.assertEquals(Area(0, 0), self.vision.area_at(Position(2, 3)))
        self.assertEquals(Area(0, 0), self.vision.area_at(Position(-1, -1)))
        self.assertEquals(None, self.vision.area_at(Position(-10, -10)))
        self.assertEquals(Area(9, 9), self.vision.area_at(Position(90, 90)))
        self.assertEquals(Area(10, 9), self.vision.area_at(Position(100, 90)))
        self.assertEquals(None, self.vision.area_at(Position(110, 110)))

    def testAreasAttachedToVisibleAreas(self):
        area = self.vision.area_at(Position(12, 13))
        self.assertEquals(9, len(area.linked))
        self.assertTrue(Area(0, 0) in list(area.linked))
        self.assertTrue(Area(2, 2) in list(area.linked))

    def testListenersAttachToSingleArea(self):
        listener = MockPlayerConnection(self.lactor)
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
        self.assertEquals({self.lactor: self.vision.areas[1, 1]},
            self.vision.actor_map)

    def testRemoveListener(self):
        listener = MockPlayerConnection(self.lactor)
        self.vision.add_listener(listener)
        self.vision.actor_update(self.actor1)
        self.assertEquals([("actor_update", self.actor1)], listener.messages)
        area = self.vision.area_for_actor(self.lactor)
        self.assertEquals(set([listener]), area.listeners)

        self.vision.remove_listener(listener)

        self.assertEquals(set(), area.listeners)
        self.assertEquals(dict(), self.vision.listener_actors)

    def testAllActorsAreKeptAsReferences(self):
        self.assertEquals(set([self.actor1]),
            self.vision.area_at(self.actor1.position).actors)

        self.vision.actor_removed(self.actor1)
        self.assertEquals(set([]),
            self.vision.area_at(self.actor1.position).actors)

    def testEventsPropagatedToAreaListeners(self):
        listener = MockPlayerConnection(self.lactor)
        self.vision.add_listener(listener)

        self.vision.actor_update(self.actor1)
        self.assertEquals(("actor_update", self.actor1),
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

        self.vision.actor_removed(self.actor1)
        self.assertEquals(("actor_removed", self.actor1),
            listener.messages[-1])

    def testEveryPartOfTheRoomShouldBeCoveredByAVisionArea(self):
        self.assertEquals(Area(0, 0), self.vision.area_at(Position(0, 0)))
        self.assertEquals(Area(9, 9), self.vision.area_at(Position(99, 99)))
        self.assertEquals(Area(10, 10), self.vision.area_at(Position(100, 100)))
        self.assertEquals(None, self.vision.area_at(Position(110, 110)))

    def testActorMovesOutOfVisionArea(self):
        self.vision = GridVision(self.room, 10)
        self.actor1 = MockActor("actor1")
        previous = build_vector(21, 21, 25, 25)
        self.actor1.vector = previous
        self.lactor = MockActor("listener1")
        self.lactor.vector = build_vector(11, 11, 15, 15)

        # add actor and listener
        self.vision.add_actor(self.actor1)
        self.vision.add_actor(self.lactor)
        listener = MockPlayerConnection(self.lactor)
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
        self.vision.add_actor(self.actor1)
        self.vision.add_actor(self.lactor)
        listener = MockPlayerConnection(self.lactor)
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
        self.vision.add_actor(self.actor1)
        self.vision.add_actor(self.lactor)
        listener = MockPlayerConnection(self.lactor)
        self.vision.add_listener(listener)

        # change vector to area outside vision distance
        self.actor1.vector = build_vector(45, 45, 55, 55)
        self.vision.actor_vector_changed(self.actor1, previous)

        self.assertEquals([], listener.messages)

    def testPlayerActorMovesIntoVisionArea(self):
        self.vision = GridVision(self.room, 10)
        self.actor1 = MockActor("actor1")
        self.actor1.vector = build_vector(35, 35, 45, 45)
        self.lactor = MockActor("listener1")
        previous = build_vector(11, 11, 15, 15)
        self.lactor.vector = previous

        # add actors and listener
        self.vision.add_actor(self.actor1)
        self.vision.add_actor(self.lactor)
        listener = MockPlayerConnection(self.lactor)
        self.vision.add_listener(listener)

        # change vector to area outside vision distance
        self.lactor.vector = build_vector(25, 25, 30, 30)
        self.vision.actor_vector_changed(self.lactor, previous)

        self.assertEquals([
            ("actor_update", self.actor1),
            ("actor_vector_changed", self.lactor, previous),
            ], listener.messages)
        self.assertEquals(listener,
            self.vision.area_for_actor(self.lactor).listeners.pop())

    def testPlayerActorMovesOutOfVisionArea(self):
        self.vision = GridVision(self.room, 10)
        self.actor1 = MockActor("actor1")
        self.actor1.vector = build_vector(25, 25, 45, 45)
        self.lactor = MockActor("listener1")
        previous = build_vector(25, 25, 30, 30)
        self.lactor.vector = previous

        # add actors and listener
        self.vision.add_actor(self.actor1)
        self.vision.add_actor(self.lactor)
        listener = MockPlayerConnection(self.lactor)
        self.vision.add_listener(listener)

        # change vector to area outside vision distance
        self.lactor.vector = build_vector(41, 41, 55, 55)
        self.vision.actor_vector_changed(self.lactor, previous)

        self.assertEquals([
            ("actor_removed", self.actor1),
            ("actor_vector_changed", self.lactor, previous),
            ], listener.messages)


    def testPlayerActorMovesInNonVisibleArea(self):
        self.vision = GridVision(self.room, 10)
        self.actor1 = MockActor("actor1")
        self.actor1.vector = build_vector(35, 35, 45, 45)
        self.lactor = MockActor("listener1")
        previous = build_vector(11, 11, 15, 15)
        self.lactor.vector = previous

        # add actors and listener
        self.vision.add_actor(self.actor1)
        self.vision.add_actor(self.lactor)
        listener = MockPlayerConnection(self.lactor)
        self.vision.add_listener(listener)

        # change vector to area outside vision distance
        self.lactor.vector = build_vector(1, 1, 5, 5)
        self.vision.actor_vector_changed(self.lactor, previous)

        self.assertEquals([
            ("actor_vector_changed", self.lactor, previous),
            ], listener.messages)

    def testMovesMoreThanOneArea(self):
        # same as move into vision test but moves longer distance
        self.vision = GridVision(self.room, 10)
        self.actor1 = MockActor("actor1")
        self.actor1.vector = build_vector(85, 85, 95, 95)
        self.lactor = MockActor("listener1")
        previous = build_vector(11, 11, 15, 15)
        self.lactor.vector = previous

        # add actors and listener
        self.vision.add_actor(self.actor1)
        self.vision.add_actor(self.lactor)
        listener = MockPlayerConnection(self.lactor)
        self.vision.add_listener(listener)

        # change vector to area outside vision distance
        self.lactor.vector = build_vector(85, 85, 95, 95)
        self.vision.actor_vector_changed(self.lactor, previous)

        self.assertEquals([
            ("actor_update", self.actor1),
            ("actor_vector_changed", self.lactor, previous),
            ], listener.messages)

    def testAbsolutePositionRoom(self):
        self.room = MockRoom("game1", "map1.roomq")
        self.room.topleft = Position(100, 0)
        self.room.bottomright = Position(200, 100)
        self.vision = GridVision(self.room, 10)
        self.actor1 = MockActor("actor1")
        self.actor1.vector = build_vector(1, 1, 5, 5)

        self.room.put_actor(self.actor1)

    def testAddRemoveActorFromVision(self):
        self.vision = GridVision(self.room, 10)
        self.actor1 = MockActor("actor1")
        self.lactor = MockActor("listener1")

        self.vision.add_actor(self.actor1)

        self.assertEquals({self.actor1: self.vision.areas[0, 0]},
            self.vision.actor_map)
        self.assertEquals({}, self.vision.listener_actors)
