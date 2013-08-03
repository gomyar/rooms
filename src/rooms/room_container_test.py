
import unittest

from room import Room
from room_container import RoomContainer
from area import Area

class MockContainer(object):
    def __init__(self):
        self.rooms = dict()

    def load_room(self, room_id):
        return self.rooms[room_id]

    def save_room(self, room):
        self.rooms[room.room_id] = room

class RoomContainerTest(unittest.TestCase):
    def setUp(self):
        self.mock_container = MockContainer()
        self.mock_container.save_room(Room("room1"))
        self.room_container = RoomContainer(Area(), self.mock_container)
        self.room_container._room_map = {'room1':{'dbase_id':'room1'},
            'room2':{'dbase_id':'room2'}}

    def testLoadARoom(self):
        room1 = self.room_container['room1']

        self.assertEquals("room1", room1.room_id)

    def testSaveARoom(self):
        room2 = Room('room2')
        self.room_container['room2'] = room2

        self.assertEquals(room2, self.mock_container.rooms['room2'])
        self.assertEquals(room2,
            self.room_container["room2"])
