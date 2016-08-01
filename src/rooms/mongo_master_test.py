
import unittest
from mock import Mock

from rooms.container import Container
from rooms.geography.basic_geography import BasicGeography
from rooms.dbase.mongo_dbase import MongoDBase
from rooms.mongo_master import Master
from rooms.testutils import MockDbase


class MasterTest(unittest.TestCase):
    def setUp(self):
        self.db = MockDbase()
        self.container = Container(self.db, None, None, None)

        self.master = Master(self.container)


        # room states
        #   pending - waiting for pickup by a node
        #   active - currently loaded into a node
        #   inactive - not loaded, no connected players in room

        #   deactivating? - node is shutting this rooms down (send wait)


    def testPlayerCreatesGame(self):
        self.assertEquals({'actors': {}, 'rooms': {}}, self.db.dbases)

        game = self.master.create_game("bob")
        self.assertEquals('games_0', game.game_id)

        # create game in db
        self.assertEquals({
            '__type__': 'Game',
            '_id': 'games_0',
            'description': None,
            'name': None,
            'owner_id': u'bob'},
            self.db.dbases['games']['games_0'])

    def testPlayerJoinsGame(self):
        self.master.create_game("bob")
        self.master.join_game("bob", 'game_0')

        # figure out start room
        # call game_start

        # if room active and node active
        #   find/create player object
        #     - create player token, save to db
        #   return node host
        # else
        #   if room doesnt exist
        #     create room skeleton - "pending"
        #   if room exists, and is "inactive", set to "pending"
        # return wait

        self.assertEquals(1, len(self.db.dbases['rooms']))
        self.assertEquals({
            '_id': 'rooms_0',
            'state': {},
            'room_id': '1',
            'game_id': '1',
        }, self.db.dbases['rooms']['rooms_0'])


    def testPlayerCallsJoinTwice(self):
        # player accidentally calls join game twice
        pass
