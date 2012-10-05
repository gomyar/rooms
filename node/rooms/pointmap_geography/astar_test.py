
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

    def testCreatespacedPointMap(self):
        point_map = PointMap(70, 50, 10)
        self.assertEquals(Point(20, 20), point_map[20, 20])
        self.assertEquals(70, point_map.width)
        self.assertEquals(50, point_map.height)
        self.assertEquals(set([(0, 10), (10, 10), (10, 0)]),
            set(point_map[0, 0].connected_points()))
        self.assertEquals(set([(20, 0), (40, 0), (20, 10), (30, 10), (40, 10)]),
            set(point_map[30, 0].connected_points()))

        point_map.make_impassable((30, 10))

        self.assertEquals(set([(20, 0), (40, 0), (20, 10), (40, 10)]),
            set(point_map[30, 0].connected_points()))

        point_map.make_impassable((30, 20), (30, 30))
        self.assertTrue((30, 20) not in set(point_map[20, 20].connected_points()))
        self.assertTrue((30, 30) not in set(point_map[20, 20].connected_points()))


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

    def testCanUseAStarTwice(self):
        point_map = PointMap(7, 5)
        point_map.make_impassable((3, 1), (3, 3))

        astar = AStar(point_map)
        path = astar.find_path(point_map[(1, 2)], point_map[(5, 2)])
        self.assertEquals([(1, 2), (2, 1), (3, 0), (4, 1), (5, 2)], path)

        path = astar.find_path(point_map[(1, 2)], point_map[(5, 2)])
        self.assertEquals([(1, 2), (2, 1), (3, 0), (4, 1), (5, 2)], path)
