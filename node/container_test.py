
import unittest

from room import Room
from area import Area

from container import _encode
from container import _decode

class ContainerTest(unittest.TestCase):
    def setUp(self):
        self.area = Area()
        self.area.rooms['lobby'] = Room('lobby')

    def testJsonPickle(self):
        pickled = _encode(self.area)
        unpickled = _decode(pickled)
        self.assertEquals(self.area.rooms['lobby'], unpickled.rooms['lobby'])
