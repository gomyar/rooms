
import unittest

import rooms.waypoint
from rooms.waypoint import Path

from linearopen_intercept import plot_intercept_point_from
from linearopen_intercept import match_path_from
from linearopen_intercept import range_cutoff


class path_vectorTest(unittest.TestCase):
    def setUp(self):
        rooms.waypoint.get_now = self._mock_get_now
        self._mock_now = 0

    def tearDown(self):
        reload(rooms.waypoint)

    def _mock_get_now(self):
        return self._mock_now

    def testIntercept(self):
        target_path = Path([(10, 10, 0), (50, 50, 100)])
        point = plot_intercept_point_from(target_path, (50, 25), 300)

        self.assertEquals((26.25, 26.25), point)

    def testMatchPath(self):
        target_path = Path([(10, 10, 0), (50, 10, 100)])
        path = match_path_from(target_path, (25, 15), 200)

        self.assertEquals([(25, 15, 0), (50, 10, 0.12747548783981963)],
            path.path)

    def testRangeCutoff(self):
        self.assertEquals((8, 8), range_cutoff(0, 0, 8, 6, 2))
