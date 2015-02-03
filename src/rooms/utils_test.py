
import unittest

from rooms.utils import sort_actor_data


class UtilsTest(unittest.TestCase):
    def setUp(self):
        self.a1 = {"actor_id": "actor1", "docked_with": None}
        self.a2 = {"actor_id": "actor2", "docked_with": "actor4"}
        self.a3 = {"actor_id": "actor3", "docked_with": "actor1"}
        self.a4 = {"actor_id": "actor4", "docked_with": "actor5"}
        self.a5 = {"actor_id": "actor5", "docked_with": None}

    def testActorDataHierarchySort(self):
        sortedlist = sort_actor_data([self.a1, self.a2, self.a3, self.a4,
            self.a5])
        self.assertEquals([self.a1, self.a3, self.a5, self.a4, self.a2],
            sortedlist)

    def testActorDataSortNoSuchParent(self):
        self.a1 = {"actor_id": "actor1", "docked_with": None}
        self.a2 = {"actor_id": "actor2", "docked_with": "actor4"}
        self.a3 = {"actor_id": "actor3", "docked_with": "not there"}
        self.a4 = {"actor_id": "actor4", "docked_with": "actor5"}
        self.a5 = {"actor_id": "actor5", "docked_with": None}

        sortedlist = sort_actor_data([self.a1, self.a2, self.a3, self.a4,
            self.a5])
        self.assertEquals([self.a1, self.a3, self.a5, self.a4, self.a2],
            sortedlist)
