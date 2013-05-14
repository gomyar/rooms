
import unittest

from rooms.controller.massive_controller import MasterController
from rooms.controller.admin_controller import AdminController
from rooms.room import Room
from rooms.area import Area
from rooms.null import Null


class MockContainer(object):
    def __init__(self, areas):
        self.areas = areas

    def load_area(self, area_id):
        return self.areas[area_id]


class MockNode(object):
    def __init__(self, container):
        self.areas = dict()
        self.container = container

    def manage_area(self, area_id):
        self.areas[area_id] = self.container.areas[area_id]


class AdminControllerTest(unittest.TestCase):
    def setUp(self):
        self.area1 = Area()
        self.area1.rooms = {
            'room1': Room("room1")
        }
        self.areas = {
            'area1': self.area1
        }
        self.mock_container = MockContainer(self.areas)
        self.node1 = MockNode(self.mock_container)
        self.master = MasterController(None, "local", 8080,
            self.mock_container)
        self.admin = AdminController(self.master)

    def testShowAdminInfo(self):
        self.master.register_node("internal.local", 8000, "external.local",
            8000)
        self.assertEquals({
            'internal.local:8000':
                {'host': 'external.local', 'port': 8000}},
            self.admin.show_nodes())

        self.node1.manage_area("area1")
        self.master.areas['area1'] = dict(players=[],
            node=('internal.local', 8000),
            area_id='area1')

        self.assertEquals({'area1': dict(players=[],
            node=('internal.local', 8000),
            area_id='area1')}, self.admin.list_areas())
