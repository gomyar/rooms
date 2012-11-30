
import unittest

import intercept
from intercept import Point
from intercept import Path


class InterceptTest(unittest.TestCase):
    def setUp(self):
        intercept._get_now = self._mock_get_now
        self._mock_now = 0

    def tearDown(self):
        reload(intercept)

    def _mock_get_now(self):
        return self._mock_now

    def testBasicPath(self):
        self.assertEquals([(Point(10, 10), 0), (Point(50, 10), 20)],
            Path([Point(10, 10), Point(50, 10)], 2).path)

    def testInterceptPoint(self):
        point1 = Point(10, 10)
        point2 = Point(50, 50)

        target_path = Path([point1, point2], 100)
        point = target_path.plot_intercept_point_from(Point(50, 25), 300)

        self.assertEquals(Point(17.8125, 17.8125), point)

    def testMatchPath(self):
        point1 = Point(10, 10)
        point2 = Point(50, 10)

        target_path = Path([point1, point2], 100)
        path = target_path.match_path_from(Point(25, 15), 200)

        self.assertEquals([(Point(15.625, 10.0), 0.053125),
            (Point(50, 10), 0.4)],
            path.path)
