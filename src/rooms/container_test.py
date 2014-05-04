
import unittest

from rooms.container import Container
from rooms.game import Game
from rooms.player import Player
from rooms.room import Room
from rooms.position import Position


class MockDbase(object):
    def __init__(self):
        self.dbases = dict()

    def load_object(self, obj_id, collection_name):
        return self.dbases.get(collection_name, dict()).get(obj_id).copy()

    def save_object(self, obj_dict, collection_name, db_id):
        obj_dict = obj_dict.copy()
        if collection_name not in self.dbases:
            self.dbases[collection_name] = dict()
        db_id = db_id or collection_name + "_" + \
            str(len(self.dbases[collection_name]))
        obj_dict['_id'] = db_id
        self.dbases[collection_name][db_id] = obj_dict
        return db_id

    def filter(self, collection_name, **fields):
        found = self.dbases.get(collection_name, dict()).values()
        found = [o for o in found if all([i in o.items() for \
            i in fields.items()])]
        found = [o.copy() for o in found]
        return found

    def filter_one(self, collection_name, **fields):
        result = self.filter(collection_name, **fields)
        return result[0] if result else None

    def object_exists(self, collection_name, **search_fields):
        return bool(self.filter(collection_name, **search_fields))

    def remove(self, collection_name, **fields):
        dbase = self.dbases.get(collection_name, [])
        keep = dict()
        for k, v in dbase.items():
            if not all([i in v.items() for i in fields.items()]):
                keep[k] = v
        self.dbases[collection_name] = keep


class ContainerTest(unittest.TestCase):
    def setUp(self):
        self.dbase = MockDbase()
        self.container = Container(self.dbase)

    def testSaveGame(self):
        self.game = Game("bob")

        self.container.save_game(self.game)

        self.assertEquals({'games_0': {u'__type__': u'Game',
            '_id': 'games_0',
            u'owner_id': u'bob'}},
            self.dbase.dbases['games'])

    def testSavePlayer(self):
        self.player = Player("bob", "games_0", "rooms_0")

        self.assertFalse(self.container.player_exists("bob", "games_0"))
        self.container.save_player(self.player)
        self.assertTrue(self.container.player_exists("bob", "games_0"))

        self.assertEquals({'players_0': {u'__type__': u'Player',
            '_id': 'players_0',
            u'game_id': u'games_0',
            u'room_id': u'rooms_0',
            u'username': u'bob'}}, self.dbase.dbases['players'])

    def testLoadPlayer(self):
        self.dbase.dbases['players'] = {'players_0': {u'__type__': u'Player',
            '_id': 'players_0',
            u'game_id': u'games_1',
            u'room_id': u'rooms_10',
            u'username': u'ned'}}

        player = self.container.load_player("ned", "games_1")

        self.assertEquals("rooms_10", player.room_id)
        self.assertEquals("players_0", player._id)

        self.assertRaises(Exception,
            self.container.load_player, "ned", "nonexistant")

    def testCreatePlayer(self):
        player = self.container.create_player("ned", "games_0", "rooms_1")
        self.assertEquals("players_0", player._id)
        self.assertEquals("ned", player.username)
        self.assertEquals("games_0", player.game_id)
        self.assertEquals("rooms_1", player.room_id)

    def testOkWeveGotTheIdea(self):
        self.container.save_room(Room("games_0", "rooms_0", Position(0, 0),
            Position(50, 50), None))
        self.assertTrue(self.dbase.dbases['rooms'])
