
import unittest

from rooms.container import Container
from rooms.game import Game
from rooms.player import PlayerActor
from rooms.room import Room
from rooms.position import Position
from rooms.testutils import MockGeog
from rooms.testutils import MockNode
from rooms.testutils import MockRoomFactory
from rooms.testutils import MockRoom
from rooms.testutils import MockTimer
from rooms.testutils import MockActor


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

    def update_object_fields(self, collection_name, obj, **fields):
        objdata = self.dbases.get(collection_name, dict()).get(obj._id)
        objdata.update(fields)


class ContainerTest(unittest.TestCase):
    def setUp(self):
        self.dbase = MockDbase()
        self.geography = MockGeog()
        self.node = MockNode()
        self.room2 = Room("games_0", "room2", Position(0, 0), Position(10, 10),
            self.node)
        self.mock_room_factory = MockRoomFactory(self.room2)
        self.container = Container(self.dbase, self.geography, self.node,
            self.mock_room_factory)
        self.node.container = self.container
        MockTimer.setup_mock()

    def testSaveGame(self):
        self.game = Game("bob")

        self.container.save_game(self.game)

        self.assertEquals({'games_0': {u'__type__': u'Game',
            '_id': 'games_0',
            u'owner_id': u'bob'}},
            self.dbase.dbases['games'])

    def testSavePlayer(self):
        self.player = PlayerActor(self.room2, "player", "container_test",
            "bob", game_id="games_0", actor_id="actors_0")

        self.assertFalse(self.container.player_exists("bob", "games_0"))
        self.container.save_player(self.player)
        self.assertTrue(self.container.player_exists("bob", "games_0"))

        self.assertEquals({'actors_0': {u'__type__': u'PlayerActor',
            '_id': 'actors_0',
            u'actor_id': u'actors_0',
            u'actor_type': u'player',
            u'game_id': u'games_0',
            u'script_name': u'container_test',
            u'room_id': u'room2',
            u'username': u'bob'}}, self.dbase.dbases['actors'])

    def testLoadPlayer(self):
        self.dbase.dbases['actors'] = {'actors_0': {u'__type__': u'PlayerActor',
            '_id': 'actors_0',
            u'actor_id': u'actors_0',
            u'actor_type': u'player',
            u'game_id': u'games_1',
            u'script_name': u'container_test',
            u'room_id': u'rooms_10',
            u'username': u'ned'}}

        player = self.container.load_player("ned", "games_1")

        self.assertEquals("rooms_10", player.room_id)
        self.assertEquals("actors_0", player._id)

        self.assertRaises(Exception,
            self.container.load_player, "ned", "nonexistant")

    def testCreatePlayer(self):
        player = self.container.create_player(self.room2, "player",
            "container_test", "ned", game_id="games_0")
        self.assertEquals("actors_0", player._id)
        self.assertEquals("ned", player.username)
        self.assertEquals("games_0", player.game_id)
        self.assertEquals("room2", player.room_id)

    def testLoadRoom(self):
        self.dbase.dbases['rooms'] = {}
        self.dbase.dbases['rooms']['rooms_0'] = { "_id": "rooms_0",
            "__type__": "Room", "room_id": "room1", "game_id": "games_0",
            "topleft": {"__type__": "Position", "x": 0, "y": 0, "z": 0},
            "bottomright": {"__type__": "Position", "x": 10, "y": 10, "z": 0},
            "doors": [{"__type__": "Door", "exit_room_id": "room2", "enter_position": {"__type__": "Position", "x": 10, "y": 10, "z": 0}, "exit_position": {"__type__": "Position", "x": 10, "y": 10, "z": 0}}]
            }
        self.dbase.dbases['actors'] = {}
        self.dbase.dbases['actors']['actor1'] = \
            {"__type__": "Actor", "_id": "actor1", "actor_id": None,
            "game_id": "games_0", "room_id": "room1",
            "actor_type": "test", "model_type": "model",
            "speed": 1.0,
            "player_username": "ned",
            "state": {}, "path": [], "vector": {"__type__": "Vector",
            "start_pos": {"__type__": "Position", "x": 0, "y": 0, "z": 0},
            "start_time": 0,
            "end_pos": {"__type__": "Position", "x": 0, "y": 10, "z": 0},
            "end_time": 10,
            }, "script_name": "rooms.container_test"}
        room = self.container.load_room("games_0", "room1")
        self.assertEquals(self.geography, room.geography)
        self.assertEquals(room, self.geography.room)
        self.assertEquals(1, len(room.actors))
        self.assertEquals(room, room.actors.values()[0].room)
        self.assertEquals(self.node, room.node)
        self.assertEquals(1, len(room.doors))

    def testCreateRoom(self):
        room = self.container.create_room("game1", "room2")
        room_dict = self.dbase.dbases['rooms']['rooms_0']
        self.assertEquals('room2', room_dict['room_id'])
        self.assertEquals(self.node, room.node)
        self.assertEquals(self.geography, room.geography)

    def testCreateExistingRoom(self):
        self.dbase.dbases['rooms'] = dict()
        self.dbase.dbases['rooms']['rooms_0'] = { "_id": "rooms_0",
            "__type__": "Room", "room_id": "room1", "game_id": "games_0",
            "topleft": {"__type__": "Position", "x": 0, "y": 0, "z": 0},
            "bottomright": {"__type__": "Position", "x": 10, "y": 10, "z": 0},
            }

        self.assertRaises(Exception, self.container.create_room, "games_0",
            "room1")

    def testSaveRoom(self):
        room = Room("game1", "room1", Position(0, 0), Position(10, 10),
            self.node)
        actor = room.create_actor("mock_actor", "rooms.room_test")
        self.container.save_room(room)
        room_dict = self.dbase.dbases['rooms']['rooms_0']
        self.assertEquals('room1', room_dict['room_id'])
        actor_dict = self.dbase.dbases['actors'][actor.actor_id]
        self.assertEquals({u'__type__': u'Actor',
            '_id': 'actors_0',
            u'actor_id': None,
            u'actor_type': u'mock_actor',
            u'game_id': u'game1',
            u'path': [],
            u'player_username': None,
            u'room_id': u'room1',
            u'script_name': u'rooms.room_test',
            u'speed': 1.0,
            u'state': {},
            u'vector': {u'__type__': u'Vector',
                        u'end_pos': {u'__type__': u'Position',
                                    u'x': 0.0,
                                    u'y': 0.0,
                                    u'z': 0.0},
                        u'end_time': 0.0,
                        u'start_pos': {u'__type__': u'Position',
                                        u'x': 0.0,
                                        u'y': 0.0,
                                        u'z': 0.0},
                        u'start_time': 0}}
            , actor_dict)

    def testOkWeveGotTheIdea(self):
        self.container.save_room(Room("games_0", "rooms_0", Position(0, 0),
            Position(50, 50), self.node))
        self.assertTrue(self.dbase.dbases['rooms'])

    def testSaveActor(self):
        room = self.container.create_room("game1", "room2")
        actor = room.create_actor("mock_actor", "rooms.room_test")
        self.container.save_actor(actor)
        self.assertEquals({u'__type__': u'Actor',
            '_id': 'actors_0',
            u'actor_id': None,
            u'actor_type': u'mock_actor',
            u'game_id': u'games_0',
            u'path': [],
            u'player_username': None,
            u'room_id': u'room2',
            u'script_name': u'rooms.room_test',
            u'speed': 1.0,
            u'state': {u'created': True},
            u'vector': {u'__type__': u'Vector',
                        u'end_pos': {u'__type__': u'Position',
                                    u'x': 0.0,
                                    u'y': 0.0,
                                    u'z': 0.0},
                        u'end_time': 0.0,
                        u'start_pos': {u'__type__': u'Position',
                                        u'x': 0.0,
                                        u'y': 0.0,
                                        u'z': 0.0},
                        u'start_time': 0}}
            , self.dbase.dbases['actors']['actors_0'])

        actor.state.testme = "value1"
        self.container.save_actor(actor)
        self.assertEquals({u'created': True, u'testme': u'value1'},
            self.dbase.dbases['actors']['actors_0']['state'])

    def testUpdateActor(self):
        actor = MockActor("actor1")
        actor._id = "actor1"

        self.dbase.dbases['actors'] = {}
        self.dbase.dbases['actors']['actor1'] = {'_id': "actor1"}
        self.dbase.dbases['actors']['actor2'] = {'_id': "actor2"}

        self.container.update_actor(actor, room_id="room2")

        self.assertEquals({'_id': "actor1", "room_id": "room2"},
            self.dbase.dbases['actors']['actor1'])
        self.assertEquals({'_id': "actor2"},
            self.dbase.dbases['actors']['actor2'])
