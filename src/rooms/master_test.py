

import unittest

from rooms.master import Master
from rooms.master import RegisteredNode
from rooms.container import Container


class MockDbase(object):
    def __init__(self):
        self.dbases = dict()

    def load_object(self, obj_id, dbase_name):
        return self.dbases.get(dbase_name, dict()).get(obj_id)

    def save_object(self, obj_dict, dbase_name, db_id):
        obj_dict = obj_dict.copy()
        if dbase_name not in self.dbases:
            self.dbases[dbase_name] = dict()
        db_id = db_id or dbase_name + "_" + str(len(self.dbases[dbase_name]))
        obj_dict['_id'] = db_id
        self.dbases[dbase_name][db_id] = obj_dict
        return db_id

    def filter(self, dbase_name, **fields):
        found = self.dbases.get(dbase_name, dict()).values()
        found = [o for o in found if all([i in o.items() for i in fields.items()])]
        found = [o.copy() for o in found]
        return found

    def filter_one(self, dbase_name, **fields):
        result = self.filter(dbase_name, **fields)
        return result[0] if result else None


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
        self.client = self
        self.host = "localhost"
        self.port = 8000
        self.external_host = "external.com"
        self.external_port = 80

    def manage_area(self, game_id, area_id):
        self.managed_areas.append((game_id, area_id))

    def player_joins(self, username, game_id):
        self.players.append(username)
        return dict(token="TOKEN")


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
        pass

    def testNodeDeregisters(self):
        # node deregisters. node must send deregistering, then deregistered,
        # in between, new join requests for any game areas are queued
        pass
