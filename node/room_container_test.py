
import unittest

from room import Room
from room_container import RoomContainer
from area import Area

class RoomContainerTest(unittest.TestCase):
    def setUp(self):
        self.room_container = RoomContainer(Area())
        self.room_container.load_room = self._mock_load_room
        self.room_container.save_room = self._mock_save_room
        self.saved_rooms = dict()
        self.room_container._room_map = {'room1':'room1', 'room2':'room2'}

    def _mock_load_room(self, room_id):
        return Room(room_id)

    def _mock_save_room(self, room_id, room):
        self.saved_rooms[room_id] = room
        return "random+"+room_id

    def testLoadARoom(self):
        room1 = self.room_container['room1']

        self.assertEquals("room1", room1.room_id)

    def testSaveARoom(self):
        room2 = Room('room2')
        self.room_container['room2'] = room2

        self.assertEquals(room2, self.saved_rooms['room2'])
        self.assertEquals("random+room2",
            self.room_container._room_map["room2"])
