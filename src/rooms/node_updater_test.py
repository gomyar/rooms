
import unittest

from rooms.testutils import MockDbase
from rooms.container import Container
from rooms.node import Node
from rooms.node_updater import NodeUpdater

from rooms.testutils import MockTimer


class NodeUpdaterTest(unittest.TestCase):
    def setUp(self):
        self.dbase = MockDbase()

        self.container = Container(self.dbase, None)

        self.node = Node(self.container, 'alpha', '192.168.0.11')
        self.updater = NodeUpdater(self.node)

        MockTimer.setup_mock()

    def tearDown(self):
        MockTimer.teardown_mock()

    def testUpdate(self):
        self.updater.send_onlinenode_update()
        self.assertEquals(
            {'_id': 'online_nodes_0', 'host': '192.168.0.11', 'name': 'alpha',
             'uptime': 0, 'load': 0.0, '__type__': 'OnlineNode',},
            self.container.dbase.dbases['online_nodes']['online_nodes_0'])
