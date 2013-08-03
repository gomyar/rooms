
import unittest

from rooms.master_controller import MasterController
from rooms.container import Container
from rooms.game import Game
from rooms.player import Player


def create_game(game):
    game.player_script = "player_script_1"


class MockNode(object):
    def __init__(self):
        self.game_script = "rooms.master_controller_test"


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


class MockContainer(Container):
    def __init__(self, dbase):
        super(MockContainer, self).__init__(dbase, None, None)

    def create_player(self, username, game_id):
        player = Player(username, game_id)
        player.game_id = game_id
        self._players.append(player)


class MasterControllerTest(unittest.TestCase):
    def setUp(self):
        self.node = MockNode()
        self.dbase = MockDbase()
        self.container = MockContainer(self.dbase)

        self.master = MasterController(self.node, "local.com", 8081,
            self.container)

    def testCreateGame(self):
        game = self.master.create_game("owner", {})
        self.assertEquals("player_script_1", game.player_script)
        self.assertEquals([{'game_id': '0', 'owner': 'owner'}],
            self.master.list_games())

    def testPlayerJoins(self):
        game = self.master.create_game("owner", {})
        result = self.master.join_game("bob", "0")

        self.assertEquals("bob", self.dbase.dbases['players']['0']['username'])
        self.assertEquals("0", self.dbase.dbases['players']['0']['game_id'])

        self.assertEquals({'host': 'node1.com', 'port': 8080}, result)
