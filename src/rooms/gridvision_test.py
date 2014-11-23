
import unittest

from rooms.position import Position
from rooms.vector import build_vector
from rooms.vector import Vector
from rooms.actor import Actor
from rooms.room import Room
from rooms.gridvision import GridVision
from rooms.gridvision import Area
from rooms.gridvision import NullArea
from rooms.views import jsonview

from rooms.player_connection import command_update
from rooms.player_connection import command_remove


class GridVisionTest(unittest.TestCase):
    def setUp(self):
        self.room = Room("game1", "map1.room1", Position(0, 0),
            Position(100, 100), None)
        self.vision = GridVision(self.room, 10)
        self.room.vision = self.vision
        self.actor1 = Actor(None, None, None, actor_id="actor1")
        self.actor1.vector = build_vector(1, 1, 5, 5)
        self.lactor = Actor(None, None, None, actor_id="listener1")
        self.lactor.vector = build_vector(11, 11, 15, 15)

        self.room.put_actor(self.actor1)
        self.room.put_actor(self.lactor)

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
        queue = self.vision.connect_vision_queue("listener1")
        self.assertEquals("sync", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])

        self.vision.actor_update(self.actor1)
        self.assertEquals("actor_update", queue.get_nowait()['command'])
        self.assertEquals(self.vision.area_for_actor(self.actor1),
            self.vision.area_at(self.actor1.vector.start_pos))

        self.vision.actor_removed(self.actor1)
        self.assertEquals("remove_actor", queue.get_nowait()['command'])
        self.assertEquals({"listener1": self.vision.areas[1, 1]},
            self.vision.actor_map)

    def testRemoveListener(self):
        queue = self.vision.connect_vision_queue("listener1")
        self.vision.actor_update(self.actor1)
        self.assertEquals("sync", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])
        area = self.vision.area_for_actor(self.lactor)
        self.assertEquals(set(["listener1"]), area.actor_queues)

        self.vision.disconnect_vision_queue("listener1", queue)

        self.assertEquals(set(), area.actor_queues)
        self.assertEquals(dict(), self.vision.actor_queues)

    def testAllActorsAreKeptAsReferences(self):
        self.assertEquals(set([self.actor1]),
            self.vision.area_at(self.actor1.position).actors)

        self.vision.actor_removed(self.actor1)
        self.assertEquals(set([]),
            self.vision.area_at(self.actor1.position).actors)

    def testEveryPartOfTheRoomShouldBeCoveredByAVisionArea(self):
        self.assertEquals(Area(0, 0), self.vision.area_at(Position(0, 0)))
        self.assertEquals(Area(9, 9), self.vision.area_at(Position(99, 99)))
        self.assertEquals(Area(10, 10), self.vision.area_at(Position(100, 100)))
        self.assertEquals(None, self.vision.area_at(Position(110, 110)))

    def testActorMovesOutOfVisionArea(self):
        self.actor1.position = Position(21, 21)
        self.lactor.position = Position(11, 11)

        queue = self.vision.connect_vision_queue("listener1")
        self.assertEquals("sync", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])

        # change vector to area outside vision distance
        self.actor1.vector = build_vector(35, 35, 45, 45)
        previous = build_vector(21, 21, 21, 21)
        self.vision.actor_vector_changed(self.actor1, previous)

        self.assertEquals("remove_actor", queue.get_nowait()['command'])

    def testActorMovesIntoVisionArea(self):
        previous = build_vector(35, 35, 45, 45)
        self.actor1.position = Position(35, 35)
        self.lactor.vector = build_vector(11, 11, 15, 15)

        # add actor and listener
        queue = self.vision.connect_vision_queue("listener1")
        self.assertEquals("sync", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])

        # change vector to area outside vision distance
        self.actor1.vector = build_vector(21, 21, 25, 25)
        self.vision.actor_vector_changed(self.actor1, previous)

        command = queue.get_nowait()
        self.assertEquals("actor_update", command['command'])
        self.assertEquals("actor1", command['actor_id'])

    def testActorMovesInNonVisibleAreas(self):
        previous = build_vector(35, 35, 45, 45)
        self.actor1.position = Position(35, 35)
        self.lactor.vector = build_vector(11, 11, 15, 15)

        # add actor and listener
        queue = self.vision.connect_vision_queue("listener1")
        self.assertEquals("sync", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])

        # change vector to area outside vision distance
        self.actor1.vector = build_vector(45, 45, 55, 55)
        self.vision.actor_vector_changed(self.actor1, previous)

        self.assertTrue(queue.empty())

    def testPlayerActorMovesIntoVisionArea(self):
        self.actor1.position = Position(35, 35)
        previous = build_vector(11, 11, 15, 15)
        self.lactor.vector = previous

        # add actors and listener
        queue = self.vision.connect_vision_queue("listener1")
        self.assertEquals("sync", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])

        # change vector to area outside vision distance
        self.lactor.vector = build_vector(25, 25, 30, 30)
        self.vision.actor_vector_changed(self.lactor, previous)

        self.assertEquals("actor_update", queue.get_nowait()['command'])
        self.assertEquals(set(["listener1"]),
            self.vision.area_for_actor(self.lactor).actor_queues)

    def testPlayerActorMovesOutOfVisionArea(self):
        queue = self.vision.connect_vision_queue("listener1")
        self.assertEquals("sync", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])

        # change vector to area outside vision distance
        self.lactor.vector = build_vector(41, 41, 55, 55)
        self.vision.actor_vector_changed(self.lactor,
            build_vector(25, 25, 30, 30))

        remove_event = queue.get_nowait()
        self.assertEquals("remove_actor", remove_event['command'])
        vector_event = queue.get_nowait()
        self.assertEquals("actor_update", vector_event['command'])

    def testPlayerActorMovesInNonVisibleArea(self):
        queue = self.vision.connect_vision_queue("listener1")
        self.assertEquals("sync", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])

        # change vector to area outside vision distance
        self.lactor.vector = build_vector(1, 1, 5, 5)
        previous = build_vector(11, 11, 15, 15)
        self.vision.actor_vector_changed(self.lactor, previous)

        self.assertEquals("actor_update", queue.get_nowait()['command'])

    def testMovesMoreThanOneArea(self):
        # same as move into vision test but moves longer distance
        self.actor1.position = Position(85, 85)
        previous = build_vector(11, 11, 15, 15)
        self.lactor.vector = previous

        # add actors and listener
        queue = self.vision.connect_vision_queue("listener1")
        self.assertEquals("sync", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])

        # change vector to area outside vision distance
        self.lactor.vector = build_vector(85, 85, 95, 95)
        self.vision.actor_vector_changed(self.lactor, previous)

        self.assertEquals("actor_update", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])

    def testAbsolutePositionRoom(self):
        self.room = Room("game1", "map1.room1", Position(100, 0),
            Position(200, 100), None)
        self.vision = GridVision(self.room, 10)
        self.room.vision = self.vision

        self.actor1 = Actor(None, None, None, actor_id="actor1")
        self.actor1.vector = build_vector(1, 1, 5, 5)

        self.room.put_actor(self.actor1)

    def testConnectToRoomWithoutActor(self):
        pass
        # wait for actor to be added to room
        # on add, send sync

    def testConnectVisionQueue(self):
        self.vision = GridVision(self.room, 10)
        self.actor1 = Actor(None, None, None, actor_id="actor1")

        self.room.put_actor(self.actor1)
        self.vision.add_actor(self.actor1)

        queue = self.vision.connect_vision_queue("actor1")

        self.assertEquals("sync", queue.get_nowait()["command"])
        self.assertEquals("actor_update", queue.get_nowait()["command"])

    def testDisconnectVisionQueue(self):
        queue = self.vision.connect_vision_queue("actor1")

        self.assertEquals(Area(0, 0), self.vision.area_for_actor(self.actor1))
        self.assertEquals({"actor1"}, self.vision.area_for_actor(self.actor1
            ).actor_queues)

        self.vision.disconnect_vision_queue("actor1", queue)

        self.assertEquals(Area(0, 0), self.vision.area_for_actor(self.actor1))
        self.assertEquals(set(),
            self.vision.area_for_actor(self.actor1).actor_queues)

    def testDisconnectVisionQueueAfterActorLeaves(self):
        pass
        # leaving thisone for now as the disconnect is done in player_connects

    def testConnectVisionQueueNoActor(self):
        self.room = Room("game1", "map1.room1", Position(0, 0),
            Position(100, 100), None)
        self.vision = GridVision(self.room, 10)
        self.room.vision = self.vision

        queue = self.vision.connect_vision_queue("actor1")

        self.assertTrue(queue.empty())

        self.actor1 = Actor(None, None, None, actor_id="actor1")
        self.vision.add_actor(self.actor1)

        self.assertEquals("sync", queue.get_nowait()["command"])
        self.assertEquals("actor_update", queue.get_nowait()["command"])

    def testEventsPropagatedToQueues(self):
        self.room = Room("game1", "map1.room1", Position(0, 0),
            Position(100, 100), None)
        self.vision = GridVision(self.room, 10)
        self.room.vision = self.vision

        queue = self.vision.connect_vision_queue("listener1")

        self.vision.add_actor(self.lactor)

        self.assertEquals("sync", queue.get_nowait()["command"])
        self.assertEquals("actor_update", queue.get_nowait()["command"])

        self.actor1 = Actor(None, None, None, actor_id="actor1")
        self.vision.add_actor(self.actor1)
        self.assertEquals("actor_update", queue.get_nowait()["command"])

        self.vision.actor_update(self.actor1)
        self.assertEquals(command_update(self.actor1), queue.get_nowait())

        previous = Vector(Position(2, 2), 0, Position(4, 4), 1)
        self.vision.actor_vector_changed(self.actor1, previous)
        self.assertEquals(command_update(self.actor1), queue.get_nowait())

        self.vision.actor_state_changed(self.actor1)
        self.assertEquals(command_update(self.actor1), queue.get_nowait())

        self.vision.actor_becomes_invisible(self.actor1)
        self.assertEquals(command_remove(self.actor1), queue.get_nowait())

        self.vision.actor_becomes_visible(self.actor1)
        self.assertEquals(command_update(self.actor1), queue.get_nowait())

        self.vision.actor_removed(self.actor1)
        self.assertEquals(command_remove(self.actor1), queue.get_nowait())
