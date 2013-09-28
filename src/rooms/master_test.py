

import unittest

from rooms.master import Master
from rooms.master import RegisteredNode
from rooms.container import Container
from rooms.container_test import MockDbase


class MockGameScript(object):
    def __init__(self):
        self._game = None
        self._options = {}

    def create_game(self, game, **options):
        self._game = game
        self._options = options
        area = game.create_area("area1")
        area.create_room("room1", (0, 0))

    def player_joins(self, game, player):
        player.area_id = "area1"
        player.room_id = "room1"


class MockNodeClient(object):
    def __init__(self):
        self.managed_areas = []
        self.players = []
        self.admins = []
        self.client = self
        self.host = "localhost"
        self.port = 8000
        self.external_host = "external.com"
        self.external_port = 80
        self.active = True

    def manage_area(self, game_id, area_id):
        self.managed_areas.append((game_id, area_id))

    def player_joins(self, username, game_id):
        self.players.append(username)
        return dict(token="TOKEN")

    def load_from_limbo(self, game_id, area_id):
        self.loaded_limbo = area_id

    def send_message(self, from_actor_id, actor_id, game_id, area_id, room_id,
            message):
        self.message_sent = (from_actor_id, actor_id, game_id, area_id, room_id,
            message)

    def admin_show_area(self, game_id, area_id):
        return {"game_id": game_id, "area_id": area_id, "mock": True}

    def admin_joins(self, username, game_id, area_id, room_id):
        self.admins.append(username)
        return dict(token="ADMIN")

    def stop_game(self, game_id):
        self.stop_called = game_id


class MasterTest(unittest.TestCase):
    def setUp(self):
        self.dbase = MockDbase()
        self.game_script = MockGameScript()

        self.master = Master(
            "host.com", 9000,
            Container(self.dbase, None, None),
            self.game_script)

    def testCreateGame(self):
        # player starts a new game
        self.master.create_game("bob")
        self.assertEquals(1, len(self.dbase.dbases['games']))
        self.assertEquals("bob", self.dbase.dbases['games']['games_0']['owner_id'])

    def testListGames(self):
        self.master.create_game("bob")

        self.assertEquals([{'owner': 'bob', 'game_id': 'games_0',
            'start_areas': []}], self.master.list_games())

        self.master.create_game("ray")

        self.assertEquals([{'owner': 'ray', 'game_id': 'games_1',
            'start_areas': []}, {'owner': 'bob', 'game_id': 'games_0',
            'start_areas': []}], self.master.list_games())

    def testEndGame(self):
        # player ends own game
        pass

    def testNodeRegisters(self):
        # node registers with master
        self.master.register_node("10.10.10.1", 8081, "node1.com", 8082)
        self.assertEquals(RegisteredNode("10.10.10.1", 8081, "node1.com", 8082),
            self.master.nodes["10.10.10.1", 8081])

    def testRequestNode(self):
        mock_node = MockNodeClient()
        self.master.nodes[('10.10.10.1', 8080)] = mock_node
        self.master.areas["games_0", "area1"] = dict(node=("10.10.10.1", 8080))

        self.assertEquals(mock_node, self.master._request_node(
            "games_0", "area1"))

    def testRequestNodeNotManaging(self):
        mock_node = MockNodeClient()
        self.master.nodes[('10.10.10.1', 8080)] = mock_node

        self.assertEquals(mock_node, self.master._request_node(
            "games_0", "area1"))

        self.assertEquals({
            ('games_0', 'area1'): {'area_id': 'area1',
            'game_id': 'games_0',
            'node': ('localhost', 8000)}}, self.master.areas)

    def testJoinGame(self):
        # node must exist
        self.mock_node = MockNodeClient()
        self.master.nodes[('10.10.10.1', 8080)] = self.mock_node
        # game must exist
        game_id = self.master.create_game("bob")
        # player joins a game
        node_info = self.master.join_game("bob", game_id)
        self.assertEquals({'host': 'external.com',
            'port': 80, 'token': 'TOKEN'}, node_info)
        # node is requested
        # player join sent to node
        self.assertEquals("bob", self.mock_node.players[0])
        # node info sent back

        # Check player info call
        self.assertEquals([{'game_id': 'games_0', 'area_id': 'area1'}],
            self.master.player_info('bob'))

    def testPlayerConnects(self):
        self.mock_node = MockNodeClient()
        self.master.nodes[('localhost', 8000)] = self.mock_node

        self.master.create_game("owner")
        result = self.master.join_game("bob", "games_0")
        self.assertEquals({'host': 'external.com', 'port': 80,
            'token': 'TOKEN'},
            self.master.connect_to_game("bob", "games_0"))

    def testPlayerMovesAreathroughLimbo(self):
        self.mock_node = MockNodeClient()
        self.master.nodes[('localhost', 8000)] = self.mock_node
        self.master.create_game("owner")
        self.master.join_game("bob", "games_0")

        player = self.dbase.dbases['players']['players_0']
        player['area_id'] = "area2"

        self.master.player_moves_area("bob", "games_0")

        self.assertEquals('area2', self.mock_node.loaded_limbo)
        # bob joined node twice
        self.assertEquals(['bob', 'bob'], self.mock_node.players)

    def testSendMessage(self):
        self.mock_node = MockNodeClient()
        self.master.nodes[('localhost', 8000)] = self.mock_node
        self.master.send_message("actor1", "actor2", "games_0", "area1",
            "room1", "msg")
        self.assertEquals(("actor1", "actor2", "games_0", "area1", "room1",
            "msg"),
            self.mock_node.message_sent)

    def testClientNodeDeregisters(self):
        # node deregisters. node must send deregistering, then deregistered,
        # in between, new join requests for any game areas are queued
        self.mock_node = MockNodeClient()
        self.master.nodes[('localhost', 8000)] = self.mock_node

        self.assertTrue(self.master.nodes["localhost", 8000].active)
        self.master.deregister_node("localhost", 8000)
        self.assertFalse(self.master.nodes["localhost", 8000].active)

        self.master.shutdown_node("localhost", 8000)
        self.assertEquals({}, self.master.nodes)



    def testAdminJoins(self):
        self.mock_node = MockNodeClient()
        self.master.nodes[('localhost', 8000)] = self.mock_node

        game = self.master.create_game("owner")
        result = self.master.join_game("bob", "games_0")

        self.assertEquals(dict(token="ADMIN", host="external.com", port=80),
            self.master.admin_connects("bob", "games_0", "area1", "room1"))

    def testAdminListAreas(self):
        self.mock_node = MockNodeClient()
        self.master.nodes[('localhost', 8000)] = self.mock_node

        self.assertEquals({}, self.master.admin_list_areas())

        game = self.master.create_game("owner")
        result = self.master.join_game("bob", "games_0")

        self.assertEquals({"games_0:area1":
            {'area_id': 'area1', "game_id": "games_0",
            'node': ('localhost', 8000)}},
            self.master.admin_list_areas())

    def testAdminShowNodes(self):
        self.mock_node = MockNodeClient()
        self.master.nodes[('localhost', 8000)] = self.mock_node

        self.assertEquals([("localhost", 8000)],
            self.master.admin_show_nodes())

        new_mock_node = MockNodeClient()
        new_mock_node.host = "10.10.10.2"
        new_mock_node.port = 8080
        self.master.nodes[('10.10.10.2', 8080)] = new_mock_node

        self.assertEquals([("10.10.10.2", 8080), ("localhost", 8000)],
            self.master.admin_show_nodes())

    def testAdminShowArea(self):
        self.mock_node = MockNodeClient()
        self.master.nodes[('localhost', 8000)] = self.mock_node

        game = self.master.create_game("owner")
        result = self.master.join_game("bob", "games_0")

        self.assertEquals({'game_id': 'games_0', 'area_id': 'area1',
            "mock": True},
            self.master.admin_show_area("games_0", "area1"))

    def testEndGame(self):
        self.mock_node = MockNodeClient()
        self.master.nodes[('localhost', 8000)] = self.mock_node

        game = self.master.create_game("bob")
        result = self.master.join_game("bob", "games_0")

        self.master.end_game("bob", "games_0")

        self.assertEquals("games_0", self.mock_node.stop_called)
        self.assertEquals({'areas': {}, 'games': {}, 'players': {},
            'rooms': {}}, self.dbase.dbases)
