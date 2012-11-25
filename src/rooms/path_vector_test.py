
import unittest

from path_vector import Path


class PathVectorTest(unittest.TestCase):
    def setUp(self):
        self.path = Path((10, 10))

#    def testMatchPath(self):
#        self.path.set_path([(10, 10), (20, 20), (30, 30)])
#        self.path2 = Path((5, 5))
#
#        self.path2.match_path(self.path)
#
#        self.assertEquals([(5, 5), (15, 15), (25, 25)],
#            self.path2.basic_path_list())
