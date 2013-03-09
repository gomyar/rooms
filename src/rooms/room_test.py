
import unittest

from room import Room
from area import Area
from actor import Actor
from rooms.timing import _set_mock_time
from rooms.timing import _fast_forward


class RoomTest(unittest.TestCase):
    def setUp(self):
        _set_mock_time(0)

        self.area = Area()
        self.room1 = Room("room1", 100, 100)
        self.area.put_room(self.room1, (0, 0))
        self.room2 = Room("room2", 100, 100)
        self.area.put_room(self.room2, (100, 0))
        self.room3 = Room("room3", 100, 100)
        self.area.put_room(self.room3, (0, 100))

        self.area.create_door(self.room1, self.room2, (0, 0), (10, 0))
        self.area.create_door(self.room1, self.room3, (10, 0), (0, 0))

        self.area.rebuild_area_map()

        self._updates_1 = []
        self._updates_2 = []

        self._mock_slept_for = 0

    def tearDown(self):
        _set_mock_time(None)

    def _mock_sleep(self, seconds):
        self._mock_slept_for += seconds
        _fast_forward(seconds)

    def _mock_actor_added_1(self, actor):
        self._updates_1.append(("added", actor))

    def _mock_actor_added_2(self, actor):
        self._updates_2.append(("added", actor))

    def testDoorsExist(self):
        self.assertTrue(self.area.rooms['room1'].has_door_to("room2"))
        self.assertTrue(self.area.rooms['room1'].has_door_to("room3"))
        self.assertFalse(self.area.rooms['room3'].has_door_to("room2"))

    def testActorExitsThroughDoor(self):
        self.actor = Actor("actor1")
        self.actor.sleep = self._mock_sleep
        self.room1.put_actor(self.actor)

        self.actor.move_to_room("room2")

        self.assertEquals("room2", self.actor.room.room_id)
        self.assertTrue(self.actor.actor_id in self.room2.actors)
        self.assertEquals([(10, 0), (10, 0)], self.actor.path.basic_path_list())
        self.assertEquals(70.71, round(self._mock_slept_for, 2))

    def testActorWithDockedExitsThroughDoor(self):
        self.actor = Actor("actor1")
        self.actor.sleep = self._mock_sleep

        self.room1.put_actor(self.actor)

        self.child1 = Actor("child1")
        self.room1.put_actor(self.child1)
        self.actor.dock(self.child1)

        self.actor.move_to_room("room2")

        self.assertEquals("room2", self.actor.room.room_id)
        self.assertEquals("room2", self.child1.room.room_id)
        self.assertTrue(self.actor.actor_id in self.room2.actors)
        self.assertEquals([(10, 0), (10, 0)], self.actor.path.basic_path_list())
        self.assertEquals(70.71, round(self._mock_slept_for, 2))

    def testCreateActor(self):
        actor = self.room1.create_actor("itemactor", "rooms.actor_test",
            actor_id="mock1")
        self.assertEquals("mock1", actor.actor_id)
        self.assertEquals("itemactor", actor.actor_type)
        self.assertEquals("itemactor", actor.model_type)
        self.assertEquals("rooms.actor_test", actor.script.script_name)

    def testQueryActors(self):
        pass

    def testActorUpdateInSector(self):
        pass#self.fail("Restrict _actor_update to visibility range")

    def testAddRemoveActorsVisibility(self):
        self.actor1 = Actor("actor1")
        self.actor1.vision_distance = 10
        self.actor1.actor_added = self._mock_actor_added_1
        self.actor1.sleep = self._mock_sleep

        self.actor2 = Actor("actor2")
        self.actor2.actor_added = self._mock_actor_added_2
        self.actor2.sleep = self._mock_sleep

        self.room1.put_actor(self.actor1, (5, 5))
        self.room1.put_actor(self.actor2, (35, 35))

        self.assertEquals([('added', self.actor1), ('added', self.actor2)], self._updates_1)
        self.assertEquals([], self._updates_2)

        self.actor2.move_to(15, 15)

        self.assertEquals([("added", self.actor1), ("added", self.actor2)], self._updates_1)
