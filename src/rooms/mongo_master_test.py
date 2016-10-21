
import unittest
import os

from rooms.container import Container
from rooms.geography.basic_geography import BasicGeography
from rooms.dbase.mongo_dbase import MongoDBase
from rooms.mongo_master import Master
from rooms.testutils import MockDbase, MockRoom, MockRoomBuilder
from rooms.testutils import MockIDFactory
from rooms.online_node import OnlineNode

from rooms.test_scripts import master_test_script


class MasterTest(unittest.TestCase):
    # The difference between joining a game and connecting to a game is
    # when you join, a playeractor is created, when you connect, the
    # playeractor is expected to exist

    def setUp(self):
        self.db = MockDbase()
        self.container = Container(self.db, None)
        self.container.save_node(OnlineNode('alpha', '10.0.0.1'))

        self.master = Master(self.container, master_test_script)

        MockIDFactory.setup_mock()

    def tearDown(self):
        MockIDFactory.teardown_mock()

    def testPlayerCreatesGame(self):
        self.assertEquals({}, self.db.dbases['actors'])
        self.assertEquals({}, self.db.dbases['rooms'])

        game_id = self.master.create_game("bob", 'test', 'a test')
        self.assertEquals('games_0', game_id)

        # create game in db
        self.assertEquals({
            '__type__': 'Game',
            '_id': 'games_0',
            'name': 'test',
            'description': 'a test',
            'owner_id': u'bob'},
            self.db.dbases['games']['games_0'])

    def testListGamesOwnedByUser(self):
        self.assertEquals([], self.master.list_games('bob'))

        game_id = self.master.create_game('bob', 'test', 'a test')

        self.assertEquals([
            {'game_id': game_id, 'name': 'test', 'description': 'a test'}],
            self.master.list_games('bob'))

        self.assertEquals([], self.master.list_games('ned'))

    def testListAllPlayersForUser(self):
        self.assertEquals([], self.master.list_players('bob'))

        game_id = self.master.create_game('bob', 'test', 'a test')

        self.assertEquals([], self.master.list_players('bob'))

        self.master.join_game(game_id, 'bob')

        self.assertEquals([
            {'game_id': game_id, 'status': 'active'}],
            self.master.list_players('bob'))

        self.master.join_game(game_id, 'ned')

        self.assertEquals([
            {'game_id': game_id, 'status': 'active'}],
            self.master.list_players('ned'))

        # create another game
        game_id_2 = self.master.create_game('bob', 'test2', '2nd test')

        self.master.join_game(game_id_2, 'ned')

        self.assertEquals([
            {'game_id': game_id, 'status': 'active'},
            {'game_id': game_id_2, 'status': 'active'}],
            sorted(self.master.list_players('ned')))

    def testPlayerJoinsGame(self):
        game_id = self.master.create_game("bob", '', '')
        self.master.join_game(game_id, "bob")

        self.assertEquals(1, len(self.db.dbases['rooms']))
        self.assertEquals({
            '__type__': 'Room',
            '_id': 'rooms_0',
            'active': False,
            'game_id': 'games_0',
            'node_name': None,
            'requested': True,
            'room_id': 'room1',
            'state': {}}, self.db.dbases['rooms']['rooms_0'])
        self.assertEquals('bob', self.db.dbases['actors']['actors_0']['username'])

    def testPlayerTriesToJoinNonExistingGame(self):
        result = self.master.join_game('nonexitant', "ned")
        self.assertEquals({'error': 'no such game'}, result)

    def testPlayerConnectsToGame(self):
        self.container.new_token = lambda: "TOKEN1"
        game_id = self.master.create_game("bob", '', '')
        result = self.master.join_game(game_id, "ned")
        self.assertEquals({'wait': True}, result)

        # node picks up player
        self.db.dbases['rooms']['rooms_0'] = {
            "__type__": "Room", "game_id": game_id, "node_name": "alpha"
        }

        result = self.master.connect_player(game_id, 'ned')
        self.assertEquals({'actor_id': 'id1', 'host': u'10.0.0.1', 'token': 'TOKEN1'}, result)

    def testPlayerCallsJoinTwice(self):
        # player accidentally calls join game twice
        pass
