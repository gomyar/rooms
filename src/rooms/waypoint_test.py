
import unittest

import rooms.waypoint
from rooms.waypoint import Path


class PathVectorTest(unittest.TestCase):
    def setUp(self):
        self.path = Path([(10, 10)])
        rooms.waypoint.get_now = self._mock_get_now
        self._mock_now = 0.0

    def testDown(self):
        reload(rooms.waypoint)

    def _mock_get_now(self):
        return self._mock_now

#    def testMatchPath(self):
#        self.path.set_path([(10, 10), (20, 20), (30, 30)])
#        self.path2 = Path((5, 5))
#
#        self.path2.match_path(self.path)
#
#        self.assertEquals([(5, 5), (15, 15), (25, 25)],
#            self.path2.basic_path_list())

    def testXFromPath(self):
        self.path = Path([ (0.0, 0.0, 0.0), (1.0, 0.0, 1.0),
            (2.0, 0.0, 2.0), (3.0, 0.0, 3.0), (4.0, 0.0, 4.0) ])

        self.assertEquals(0.0, self.path.x())

        self._mock_now =0.5
        self.assertEquals(0.5, self.path.x())

        self._mock_now =1.5
        self.assertEquals(1.5, self.path.x())

        self._mock_now =2.5
        self.assertEquals(2.5, self.path.x())

        self._mock_now =4.5
        self.assertEquals(4.0, self.path.x())

    def testYFromPath(self):
        self.path = Path([ (0.0, 0.0, 0.0), (0.0, 1.0, 1.0),
            (0.0, 2.0, 2.0), (0.0, 3.0, 3.0), (0.0, 4.0, 4.0) ])

        self.assertEquals(0.0, self.path.y())

        self._mock_now =0.5
        self.assertEquals(0.5, self.path.y())

        self._mock_now =1.5
        self.assertEquals(1.5, self.path.y())

        self._mock_now =2.5
        self.assertEquals(2.5, self.path.y())

        self._mock_now =4.5
        self.assertEquals(4.0, self.path.y())

    def testSpeedFromPath(self):
        self.path = Path([(0, 0, 0), (100, 0, 100)])

        self.assertEquals(1, self.path.speed())

        self.path = Path([(0, 0, 0), (10, 0, 10), (30, 0, 20), (60, 0, 30)])

        self.assertEquals(1, self.path.speed())

        self._mock_now = 10.1
        self.assertEquals(2, self.path.speed())

        self._mock_now = 20.1
        self.assertEquals(3, self.path.speed())

        self._mock_now = 30.1
        self.assertEquals(0, self.path.speed())
