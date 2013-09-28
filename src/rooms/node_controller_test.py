
import unittest

from rooms.node_controller import NodeController
from rooms.player import Player
from rooms.room import Room
from rooms.area import Area


class MockMaster(object):
    def __init__(self):
        self.registered = None
        self.deregistered = None

    def register_node(self, host, port, external_host, external_port):
        self.registered = (host, port, external_host, external_port)

    def deregister_node(self, host, port):
        self.deregistered = (host, port)


class MockContainer(object):
    def __init__(self):
        self.players = dict()

    def load_player(self, username, game_id):
        return self.players[username, game_id]


class MockNode(object):
    def __init__(self, host, port, container):
        self.host = host
        self.port = port
        self.limbo_loaded = None
        self.managed_area = None
        self.container = container
        self.players = dict()
        self.admin = None
        self.areas = dict()

    def send_message(self, from_actor_id, actor_id, room_id, area_id, message):
        self.message = (from_actor_id, actor_id, room_id, area_id, message)

    def load_from_limbo(self, area_id):
        self.limbo_loaded = area_id

    def manage_area(self, game_id, area_id):
        self.managed_area = area_id

    def player_joins(self, game_id, area_id, player):
        self.players[player.username] = player

    def admin_joins(self, username, game_id, area_id, room_id):
        self.admin = (username, game_id, area_id, room_id)


class NodeControllerTest(unittest.TestCase):
    def setUp(self):
        self.master = MockMaster()
        self.container = MockContainer()
        self.player = Player("bob", "games_0")
        self.player.area_id = "area1"
        self.container.players["bob", "game1"] = self.player
        self.node = MockNode("node1.com", 80, self.container)
        self.controller = NodeController(self.node, "10.10.10.1", 8080,
            "master", 8081)
        self.controller.master = self.master

    def testRegisterWithMaster(self):
        self.controller.register_with_master()

        self.assertEquals(("10.10.10.1", 8080, "node1.com", 80),
            self.master.registered)

    def testDeregisterFromMater(self):
        self.controller.deregister_from_master()

        self.assertEquals(("10.10.10.1", 8080), self.master.deregistered)

    def testSendMessage(self):
        self.controller.send_message("from_actor", "to_actor", "room1",
            "area1", "msg")

        self.assertEquals(self.node.message, ("from_actor", "to_actor", "room1",
            "area1", "msg"))

    def testLoadFromLimbo(self):
        self.controller.load_from_limbo("area1")

        self.assertEquals("area1", self.node.limbo_loaded)

    def testManageArea(self):
        self.controller.manage_area("games_0", "area1")

        self.assertEquals("area1", self.node.managed_area)

    def testPlayerJoins(self):
        self.controller.player_joins("bob", "game1")

        self.assertEquals(dict(bob=self.player), self.node.players)

    def testAdminJoins(self):
        self.controller.admin_joins("bob", "games_0", "area1", "room1")

        self.assertEquals(("bob", "games_0", "area1", "room1"), self.node.admin)

    def testAdminShowArea(self):
        area = Area()
        self.node.areas['area1'] = area
        area.rooms['room1'] = Room("room1")

        self.assertEquals(
            {'area_id': 'area1', 'node_addr': 'node1.com', 'node_port': 80, 'active_rooms': {'room1': {'width': 50, 'visibility_grid': {'width': 50, 'gridsize': 100, 'actors': {}, 'height': 50}, 'room_id': 'room1', 'description': 'room1', 'players': 0, 'map_objects': None, 'position': (0, 0), 'height': 50}}}
            , self.controller.admin_show_area('area1'))
