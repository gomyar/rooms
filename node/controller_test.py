
import unittest

from controller import ClientController
from controller import MasterController

from wsgi_rpc import WSGIRPCClient

from node import Node
from rooms.area import Area
from rooms.instance import Instance
from rooms.room import Room

from mock import Mock


class MockContainer(object):
    def __init__(self, area, rooms):
        self.area = area
        self.rooms = rooms

    def load_area(self, area_id):
        return self.area

    def load_room(self, room_id):
        return self.rooms[room_id]


class ControllerTest(unittest.TestCase):
    def setUp(self):
        self.node = Node('', 'localhost', 8000)
        self.area = Area()
        self.area.area_name = "area1"
        self.area.entry_point_room_id = "room1"
        self.room = Room("room1")
        self.area.rooms._rooms['room1'] = self.room
        self.node.container = MockContainer(self.area, {'room1': self.room})

        self.master = MasterController('master.com', 8080)
        self.client = ClientController(self.node,
            'client.com', 8081, 'master.com', 8080)

        self.client.master = self.master
        self.master.nodes['client.com', 8081] = self.client

    def testRegisterClient(self):
        self.client.register_with_master()

        self.assertEquals({
            ('client.com', 8081): WSGIRPCClient('client.com', 8081),
        }, self.master.nodes)

    def testWsgiClientConnect(self):
        self.client.init()

        self.assertEquals(WSGIRPCClient, type(self.client.master))
        self.assertEquals(self.master.host, self.client.master.host)
        self.assertEquals(self.master.port, self.client.master.port)


    def testClientCreateInstance(self):
        self.node._random_uid = lambda: "instance1"
        self.client.create_instance("area1")

        self.assertTrue("instance1" in self.node.instances)
        self.assertEquals("area1", self.node.instances['instance1'].area.area_name)

    def testPlayerJoins(self):
        self.node._random_uid = lambda: "instance1"
        self.client.create_instance("area1")
        self.client.player_joins("instance1", "player1")

        self.assertEquals("player1", self.node.instances['instance1'].players['player1']['player'].actor_id)

    def testMasterCreateInstance(self):
        self.node._random_uid = lambda: "instance1"

        instance = self.master.create_instance("area1")
        self.assertEquals({'area_id': 'area1',
            'node': ('client.com', 8081),
            'players': [],
            'uid': 'instance1'}, instance)
