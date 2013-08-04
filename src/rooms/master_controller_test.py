
import unittest

from rooms.master_controller import MasterController
from rooms.container import Container
from rooms.game import Game
from rooms.player import Player
from rooms.master_controller import RegisteredNode


def create_game(game):
    game.player_script = "player_script_1"
    game.start_areas = [('area1', 'room1'), ('area2', 'room2')]


class MockNode(object):
    def __init__(self):
        self.game_script = "rooms.master_controller_test"


class MockClientNode(object):
    def __init__(self, host, port, external_host, external_port):
        self.host = host
        self.port = port
        self.external_host = external_host
        self.external_port = external_port
        # mock connection
        self.client = self
        self.managed_areas = []
        self.players = []
        self.active = True

    def manage_area(self, area_id):
        self.managed_areas.append(area_id)

    def player_joins(self, username, game_id):
        self.players.append(username)
        return dict(token="TOKEN")

    def load_from_limbo(self, area_id):
        pass


class MockDbase(object):
    def __init__(self):
        self.dbases = dict()

    def load_object(self, obj_id, dbase_name):
        return self.dbases.get(dbase_name, dict()).get(obj_id)

    def save_object(self, obj_dict, dbase_name, db_id):
        if dbase_name not in self.dbases:
            self.dbases[dbase_name] = dict()
        db_id = db_id or str(len(self.dbases[dbase_name]))
        obj_dict['_id'] = db_id
        self.dbases[dbase_name][db_id] = obj_dict

    def filter(self, dbase_name, **fields):
        return self.dbases.get(dbase_name, dict()).values()

    def filter_one(self, dbase_name, **fields):
        result = self.dbases.get(dbase_name, dict()).values()
        return result[0] if result else None


class MockContainer(Container):
    def __init__(self, dbase):
        super(MockContainer, self).__init__(dbase, None, None)


class MasterControllerTest(unittest.TestCase):
    def setUp(self):
        self.node = MockNode()
        self.dbase = MockDbase()
        self.container = MockContainer(self.dbase)

        self.master = MasterController(self.node, "local.com", 8081,
            self.container)
        self.master.nodes[('10.10.10.1', 8080)] = MockClientNode(
            '10.10.10.1', 8080, 'node1.com', 8082)

    def testCreateGame(self):
        game = self.master.create_game("owner", {})
        self.assertEquals("player_script_1", game.player_script)
        self.assertEquals([{'game_id': '0', 'owner': 'owner',
            'start_areas': [['area1', 'room1'], ['area2', 'room2']]}],
            self.master.list_games())

    def testPlayerJoins(self):
        game = self.master.create_game("owner", {})
        result = self.master.join_game("bob", "0", "area1", "room1")

        self.assertEquals("bob", self.dbase.dbases['players']['0']['username'])
        self.assertEquals("0", self.dbase.dbases['players']['0']['game_id'])

        # First player creates area on client node
        self.assertEquals({'host': 'node1.com', 'port': 8082, 'token': 'TOKEN'},
            result)
        client_node = self.master.nodes[('10.10.10.1', 8080)]
        self.assertEquals(['area1'], client_node.managed_areas)
        self.assertEquals(['bob'], client_node.players)

        # Check player info call
        self.assertEquals([{'game_id': '0', 'area_id': 'area1'}],
            self.master.player_info('bob'))

    def testPlayerAlreadyJoined(self):
        game = self.master.create_game("owner", {})
        result = self.master.join_game("bob", "0", "area1", "room1")
        try:
            result = self.master.join_game("bob", "0", "area1", "room1")
            self.fail("Should have thrown")
        except AssertionError, ae:
            raise
        except Exception, e:
            self.assertEquals("User bob already joined game 0", str(e))

    def testClientNodeRegisters(self):
        self.master.register_node("10.10.10.1", 8081, "node1.com", 8082)
        self.assertEquals(RegisteredNode("10.10.10.1", 8081, "node1.com", 8082),
            self.master.nodes["10.10.10.1", 8081])

    def testClientNodeDeregisters(self):
        self.assertTrue(self.master.nodes["10.10.10.1", 8080].active)
        self.master.deregister_node("10.10.10.1", 8080)
        self.assertFalse(self.master.nodes["10.10.10.1", 8080].active)

        self.master.shutdown_node("10.10.10.1", 8080)
        self.assertEquals({}, self.master.nodes)

    def testNodeInfo(self):
        game = self.master.create_game("owner", {})
        self.assertEquals({'host': 'node1.com', 'port': 8082},
            self.master.node_info('area1'))

    def testPlayerMoves(self):
        game = self.master.create_game("owner", {})
        result = self.master.join_game("bob", "0", "area1", "room1")

        self.master.nodes[('10.10.10.2', 8080)] = MockClientNode(
            '10.10.10.2', 8080, 'node2.com', 8082)

        self.master.areas = {
            'area1': {'area_id': 'area1', 'node': ('10.10.10.1', 8080)},
            'area2': {'area_id': 'area2', 'node': ('10.10.10.2', 8080)},
        }
        self.assertEquals('area1', self.dbase.dbases['players']['0']['area_id'])

        self.assertEquals(['bob'],
            self.master.nodes['10.10.10.1', 8080].players)
        self.assertEquals([], self.master.nodes['10.10.10.2', 8080].players)

        self.dbase.dbases['players']['0']['area_id'] = 'area2'

        self.master.player_moves_area("bob", "game1")

        self.assertEquals(['bob'],
            self.master.nodes['10.10.10.2', 8080].players)
