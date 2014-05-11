
import unittest

from testutils import MockTimer
from rooms.vector import Vector
from rooms.position import Position


class VectorTest(unittest.TestCase):
    def setUp(self):
        MockTimer.setup_mock()

    def tearDown(self):
        MockTimer.teardown_mock()

    def testCreation(self):
        self.vector = Vector(Position(0, 0), Position(10, 0), 2)
        self.assertEquals(Position(0, 0), self.vector.start_pos)
        self.assertEquals(Position(10, 0), self.vector.end_pos)
        self.assertEquals(0, self.vector.start_time)
        self.assertEquals(5, self.vector.end_time)
