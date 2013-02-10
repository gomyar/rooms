
import unittest

from room import Room
from area import Area
from actor import Actor


class RoomTest(unittest.TestCase):
    def setUp(self):
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

    def _mock_sleep(self, seconds):
        self._mock_slept_for = seconds

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
