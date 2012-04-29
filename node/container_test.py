
import unittest

from room import Room
from area import Area
from actor import Actor

from container import serialize_area
from container import deserialize_area

class ContainerTest(unittest.TestCase):
    def setUp(self):
        self.area = Area()
        self.area.rooms['lobby'] = Room('lobby')
        actor = Actor('actor1')
        self.area.actors['actor1'] = actor
        self.area.actor_enters(actor, 'lobby')

    def testJsonPickle(self):
        pickled = serialize_area(self.area)
        unpickled = deserialize_area(pickled)
        self.assertEquals(self.area.rooms['lobby'], unpickled.rooms['lobby'])
        self.assertEquals(self.area.actors['actor1'], unpickled.actors['actor1'])
