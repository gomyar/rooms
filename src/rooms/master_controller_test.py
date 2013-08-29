
import unittest

from rooms.master_controller import MasterController
from rooms.container import Container
from rooms.game import Game
from rooms.player import Player
from rooms.master_controller import RegisteredNode


def create_game(game):
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
        self.admins = []
        self.active = True
        self.loaded_limbo = False
        self.message_sent = None

    def manage_area(self, area_id):
        self.managed_areas.append(area_id)

    def player_joins(self, username, game_id):
        self.players.append(username)
        return dict(token="TOKEN")

    def admin_joins(self, username, area_id, room_id):
        self.admins.append(username)
        return dict(token="ADMIN")

    def load_from_limbo(self, area_id):
        self.loaded_limbo = area_id

    def send_message(self, from_actor_id, actor_id, room_id, area_id, message):
        self.message_sent = (from_actor_id, actor_id, room_id, area_id, message)

    def admin_show_area(self, area_id):
        return {'area': 'area_id', 'mock': True}


class MockDbase(object):
    def __init__(self):
        self.dbases = dict()

    def load_object(self, obj_id, dbase_name):
        return self.dbases.get(dbase_name, dict()).get(obj_id)

    def save_object(self, obj_dict, dbase_name, db_id):
        if dbase_name not in self.dbases:
            self.dbases[dbase_name] = dict()
        db_id = db_id or dbase_name + "_" + str(len(self.dbases[dbase_name]))
        obj_dict['_id'] = db_id
        self.dbases[dbase_name][db_id] = obj_dict
        return db_id

    def filter(self, dbase_name, **fields):
        found = self.dbases.get(dbase_name, dict()).values()
        return [o for o in found if all([i in o.items() for i in fields.items()])]

    def filter_one(self, dbase_name, **fields):
        result = self.filter(dbase_name, **fields)
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
        game = self.master.create_game("owner")
        self.assertEquals([{'game_id': 'games_0', 'owner': 'owner',
            'start_areas': [['area1', 'room1'], ['area2', 'room2']]}],
            self.master.list_games())

    def testPlayerJoins(self):
        game = self.master.create_game("owner")
        result = self.master.join_game("bob", "games_0", "area1", "room1")

        self.assertEquals("bob", self.dbase.dbases['players']['players_0']['username'])
        self.assertEquals("games_0", self.dbase.dbases['players']['players_0']['game_id'])

        # First player creates area on client node
        self.assertEquals({'host': 'node1.com', 'port': 8082, 'token': 'TOKEN'},
            result)
        client_node = self.master.nodes[('10.10.10.1', 8080)]
        self.assertEquals(['area1'], client_node.managed_areas)
        self.assertEquals(['bob'], client_node.players)

        # Check player info call
        self.assertEquals([{'game_id': 'games_0', 'area_id': 'area1'}],
            self.master.player_info('bob'))

    def testPlayerAlreadyJoined(self):
        game = self.master.create_game("owner")
        result = self.master.join_game("bob", "games_0", "area1", "room1")
        try:
            result = self.master.join_game("bob", "games_0", "area1", "room1")
            self.fail("Should have thrown")
        except AssertionError, ae:
            raise
        except Exception, e:
            self.assertEquals("User bob already joined game games_0", str(e))

    def testPlayerConnects(self):
        game = self.master.create_game("owner")
        result = self.master.join_game("bob", "games_0", "area1", "room1")
        self.assertEquals({'host': 'node1.com', 'port': 8082, 'token': 'TOKEN'},
            self.master.connect_to_game("bob", "games_0"))

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
        game = self.master.create_game("owner")
        self.assertEquals({'host': 'node1.com', 'port': 8082},
            self.master.node_info('area1'))

    def testPlayerMoves(self):
        game = self.master.create_game("owner")
        result = self.master.join_game("bob", "games_0", "area1", "room1")

        self.master.nodes[('10.10.10.2', 8080)] = MockClientNode(
            '10.10.10.2', 8080, 'node2.com', 8082)

        self.master.areas = {
            'area1': {'area_id': 'area1', 'node': ('10.10.10.1', 8080)},
            'area2': {'area_id': 'area2', 'node': ('10.10.10.2', 8080)},
        }
        self.assertEquals('area1', self.dbase.dbases['players']['players_0']['area_id'])

        self.assertEquals(['bob'],
            self.master.nodes['10.10.10.1', 8080].players)
        self.assertEquals([], self.master.nodes['10.10.10.2', 8080].players)

        self.dbase.dbases['players']['players_0']['area_id'] = 'area2'

        self.master.player_moves_area("bob", "games_0")

        self.assertEquals('area2',
            self.master.nodes['10.10.10.2', 8080].loaded_limbo)
        self.assertEquals(['bob'],
            self.master.nodes['10.10.10.2', 8080].players)

    def testActorMovesArea(self):
        game = self.master.create_game("owner")
        result = self.master.join_game("bob", "games_0", "area1", "room1")

        self.master.actor_moves_area("area1")
        self.assertEquals('area1',
            self.master.nodes['10.10.10.1', 8080].loaded_limbo)

    def testSendMEssage(self):
        self.master.send_message("actor1", "actor2", "room1", "area1", "msg")
        self.assertEquals(("actor1", "actor2", "room1", "area1", "msg"),
            self.master.nodes[('10.10.10.1', 8080)].message_sent)

    def testAdminJoins(self):
        game = self.master.create_game("owner")
        result = self.master.join_game("bob", "games_0", "area1", "room1")

        self.assertEquals(dict(token="ADMIN", host="node1.com", port=8082),
            self.master.admin_connects("bob", "area1", "room1"))

    def testAdminListAreas(self):
        self.assertEquals({}, self.master.admin_list_areas())

        game = self.master.create_game("owner")
        result = self.master.join_game("bob", "games_0", "area1", "room1")

        self.assertEquals({'area1':
            {'area_id': 'area1', 'node': ('10.10.10.1', 8080)}},
            self.master.admin_list_areas())

    def testAdminShowNodes(self):
        self.assertEquals([("10.10.10.1", 8080)],
            self.master.admin_show_nodes())

        self.master.nodes[('10.10.10.2', 8080)] = MockClientNode(
            '10.10.10.2', 8080, 'node2.com', 8082)

        self.assertEquals([("10.10.10.1", 8080), ("10.10.10.2", 8080)],
            self.master.admin_show_nodes())

    def testAdminShowArea(self):
        game = self.master.create_game("owner")
        result = self.master.join_game("bob", "games_0", "area1", "room1")

        self.assertEquals({'area': 'area_id', 'mock': True},
            self.master.admin_show_area("area1"))
