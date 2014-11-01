
import unittest
import time

from rooms.timer import Timer


class TimerTest(unittest.TestCase):
    def setUp(self):
        self.timer = Timer()

    def testTimer(self):
        self.assertEquals(round(self.timer._now() / 10),
            round(time.time() / 10))
