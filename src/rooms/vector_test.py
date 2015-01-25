
import unittest
import math

from testutils import MockTimer
from rooms.vector import create_vector
from rooms.position import Position


class VectorTest(unittest.TestCase):
    def setUp(self):
        MockTimer.setup_mock()

    def tearDown(self):
        MockTimer.teardown_mock()

    def testCreation(self):
        self.vector = create_vector(Position(0, 0), Position(10, 0), 2)
        self.assertEquals(Position(0, 0), self.vector.start_pos)
        self.assertEquals(Position(10, 0), self.vector.end_pos)
        self.assertEquals(0, self.vector.start_time)
        self.assertEquals(5, self.vector.end_time)

    def testCurrentPositionX(self):
        self.vector = create_vector(Position(0, 0), Position(10, 0), 2)
        MockTimer.fast_forward(1)
        self.assertEquals(2, self.vector.x)
        MockTimer.fast_forward(1)
        self.assertEquals(4, self.vector.x)

    def testCurrentPositionY(self):
        self.vector = create_vector(Position(0, 0), Position(0, 10), 2)
        MockTimer.fast_forward(1)
        self.assertEquals(2, self.vector.y)
        MockTimer.fast_forward(1)
        self.assertEquals(4, self.vector.y)

    def testCurrentPositionZ(self):
        self.vector = create_vector(Position(0, 0), Position(0, 0, 10), 2)
        MockTimer.fast_forward(1)
        self.assertEquals(2, self.vector.z)
        MockTimer.fast_forward(1)
        self.assertEquals(4, self.vector.z)

    def testAngle(self):
        self.vector = create_vector(Position(10, 0), Position(0, 0), 2)
        self.assertEquals(math.pi, self.vector.yaw())
        self.vector = create_vector(Position(0, 0), Position(10, 0), 2)
        self.assertEquals(0, self.vector.yaw())

    def testExtrapolate(self):
        self.vector = create_vector(Position(10, 0), Position(20, 0), 1)
        extrap = self.vector.extrapolate(ratio=0.5)
        self.assertEquals(Position(15, 0), extrap)
        extrap = self.vector.extrapolate(ratio=1.5)
        self.assertEquals(Position(25, 0), extrap)
