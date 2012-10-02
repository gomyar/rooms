
import unittest

from astar import AStar
from astar import PointMap
from astar import Point


class AStarTest(unittest.TestCase):
    def testCreatePointMap(self):
        point_map = PointMap(7, 5)
        self.assertEquals(Point(2, 2), point_map[2, 2])
        self.assertEquals(7, point_map.width)
        self.assertEquals(5, point_map.height)
        self.assertEquals(set([(0, 1), (1, 1), (1, 0)]),
            set(point_map[0, 0].connected_points()))
        self.assertEquals(set([(2, 0), (4, 0), (2, 1), (3, 1), (4, 1)]),
            set(point_map[3, 0].connected_points()))

        point_map.make_impassable((3, 1))

        self.assertEquals(set([(2, 0), (4, 0), (2, 1), (4, 1)]),
            set(point_map[3, 0].connected_points()))

        point_map.make_impassable((3, 2), (3, 3))
        self.assertTrue((3, 2) not in set(point_map[2, 2].connected_points()))
        self.assertTrue((3, 3) not in set(point_map[2, 2].connected_points()))

    def testExample(self):
        point_map = PointMap(7, 5)
        point_map.make_impassable((3, 1), (3, 3))

        path = AStar(point_map).find_path(point_map[(1, 2)], point_map[(5, 2)])

        self.assertEquals([(1, 2), (2, 1), (3, 0), (4, 1), (5, 2)], path)

    def testExample2(self):
        point_map = PointMap(7, 5)
        point_map.make_impassable((3, 0), (3, 3))

        path = AStar(point_map).find_path(point_map[(1, 2)], point_map[(5, 2)])

        self.assertEquals([(1, 2), (2, 3), (3, 4), (4, 3), (5, 2)], path)

    def testExample2(self):
        point_map = PointMap(7, 5)
        point_map.make_impassable((3, 0), (3, 4))

        path = AStar(point_map).find_path(point_map[(1, 2)], point_map[(5, 2)])

        self.assertEquals([], path)
