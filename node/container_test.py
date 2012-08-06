
import unittest

from rooms.room import Room
from rooms.room_container import RoomContainer
from rooms.area import Area
from rooms.actor import Actor

from container import serialize_area
from container import create_area

class MockRoomContainer(RoomContainer):
    def load_room(self, room_id):
        return self._rooms[room_id]

    def save_room(self, room_id, room):
        self._rooms[room_id] = room

class ContainerTest(unittest.TestCase):
    def setUp(self):
        self.area = Area()
        self.area.load_script("container_test")
        self.area.rooms['lobby'] = Room('lobby')
        self.area.rooms['lobby'].actors['actor1'] = Actor('actor1')

    def testJsonPickle(self):
        pickled = serialize_area(self.area)
        unpickled = create_area(pickled)
        unpickled.rooms = MockRoomContainer(self.area)
        unpickled.rooms._rooms['lobby'] = Room('lobby')
        unpickled.rooms._rooms['lobby'].actors['actor1'] = Actor('actor1')
        self.assertEquals(self.area.rooms['lobby'], unpickled.rooms['lobby'])
        self.assertEquals(self.area.rooms['lobby'].actors['actor1'],
            unpickled.rooms['lobby'].actors['actor1'])
