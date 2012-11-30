
import unittest

import intercept
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
        self.assertEquals([((10, 10), 0), ((50, 10), 20)],
            Path([(10, 10), (50, 10)], 2).path)

    def testIntercept(self):
        point1 = (10, 10)
        point2 = (50, 50)

        target_path = Path([point1, point2], 100)
        point = target_path.plot_intercept_point_from((50, 25), 300)

        self.assertEquals((17.8125, 17.8125), point)

    def testMatchPath(self):
        point1 = (10, 10)
        point2 = (50, 10)

        target_path = Path([point1, point2], 100)
        path = target_path.match_path_from((25, 15), 200)

        self.assertEquals([((15.625, 10.0), 0.053125),
            ((50, 10), 0.4)],
            path.path)
