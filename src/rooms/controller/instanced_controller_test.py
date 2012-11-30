
import unittest

from rooms.controller.instanced_controller import ClientController
from rooms.controller.instanced_controller import MasterController
from rooms.controller.instanced_controller import RegisteredNode

from rooms.wsgi_rpc import WSGIRPCClient

from rooms.node import Node
from rooms.area import Area
from rooms.instance import Instance
from rooms.room import Room
from rooms.player import Player
from rooms.game import Game

from mock import Mock


class MockContainer(object):
    def __init__(self, game, area, rooms):
        self.game = game
        self.area = area
        self.rooms = rooms
        self.player = Player("mock")

    def load_area(self, area_id):
        return self.area

    def load_room(self, room_id):
        return self.rooms[room_id]

    def get_or_create_player(self, player_id):
        return self.player

    def save_player(self, player):
        pass

    def load_game(self, game_id):
        return self.game


class ControllerTest(unittest.TestCase):
    def setUp(self):
        self.node = Node('/', 'external.com', 8082)
        self.game = Game()
        self.node.game = self.game
        self.area = Area()
        self.area.area_name = "area1"
        self.area.entry_point_room_id = "room1"
        self.game.area_map['area1'] = 'area1'
        self.game.start_areas.append('area1')
        self.game._id = "game1"
        self.room = Room("room1")
        self.area.rooms._rooms['room1'] = self.room
        self.node.container = MockContainer(self.game, self.area,
            {'room1': self.room})

        self.master = MasterController('master.com', 8080,
            self.node.container)
        self.master.create_script = Mock()
        self.client = ClientController(self.node,
            'client.com', 8081, 'master.com', 8080)

        self.client.master = self.master
        self.master.register_node('client.com', 8081, 'external.com', 8082)
        self.master.nodes['client.com', 8081].client = self.client

    def testRegisterClient(self):
        self.client.register_with_master()

        self.assertEquals({
            ('client.com', 8081): RegisteredNode('client.com', 8081,
                'external.com', 8082),
        }, self.master.nodes)

    def testWsgiClientConnect(self):
        self.client.init()

        self.assertEquals(WSGIRPCClient, type(self.client.master))
        self.assertEquals(self.master.host, self.client.master.host)
        self.assertEquals(self.master.port, self.client.master.port)


    def testClientCreateInstance(self):
        self.node._random_uid = lambda: "instance1"
        self.client.manage_area("game1", "area1")

        self.assertTrue("instance1" in self.node.instances)
        self.assertEquals("area1", self.node.instances['instance1'].area.area_name)

    def testPlayerJoins(self):
        self.node._random_uid = lambda: "instance1"
        self.client.manage_area("game1", "area1")
        self.client.player_joins("area1", "player1")

        self.assertEquals("player1", self.node.instances['instance1'].players['player1']['player'].actor_id)

    def testMasterCreateInstance(self):
        self.node._random_uid = lambda: "instance1"
        self.master._create_game = lambda: self.game

        instance = self.master.create_game("area1")
        instance.pop('area_id')
        self.assertEquals({
            'node': ('client.com', 8081),
            'players': [],
            'uid': 'instance1'}, instance)
        self.assertEquals(instance, self.master.instances['instance1'])