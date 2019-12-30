
import os
import unittest

from rooms.container import Container
from rooms.game import Game
from rooms.player import PlayerActor
from rooms.room import Room
from rooms.position import Position
from rooms.testutils import MockGeog
from rooms.testutils import MockNode
from rooms.testutils import MockRoom
from rooms.testutils import MockTimer
from rooms.testutils import MockActor
from rooms.testutils import MockDbase
from rooms.testutils import MockIDFactory
from rooms.room_builder import FileMapSource
from rooms.room_builder import RoomBuilder
from rooms.actor import Actor
from rooms.script import Script


class ContainerTest(unittest.TestCase):
    def setUp(self):
        self.dbase = MockDbase()
        self.geography = MockGeog
        self.node = MockNode()
        self.room2 = Room("games_0", "room2", self.node)
        self.room2.coords(0, 0, 10, 10)
        self.map_source = FileMapSource(os.path.join(os.path.dirname(__file__),
            "test_maps"))
        self.room_builder = RoomBuilder(self.map_source, self.node)
        self.container = Container(self.dbase, self.node)
        self.container.geography = self.geography
        self.container.room_builder = self.room_builder
        self.node.container = self.container
        MockTimer.setup_mock()
        MockIDFactory.setup_mock()

    def tearDown(self):
        MockIDFactory.teardown_mock()

    def testSaveGame(self):
        self.game = Game("bob", state={"name": "Bob's game",
                                       "description": "A game by Bob"})

        self.container.save_game(self.game)

        self.assertEquals({'games_0': {u'__type__': u'Game',
            '_id': 'games_0',
            'created_on': 0,
            'state': {
                'name': "Bob's game",
                'description': "A game by Bob",
            },
            'owner_id': 'bob'}},
            self.dbase.dbases['games'])

    def testLoadGame(self):
        self.dbase.dbases['games'] = {'games_0': {u'__type__': u'Game',
            '_id': 'games_0',
            u'name': "Bob's game",
            u'description': "A game by Bob",
            'state': {},
            'created_on': 0,
            u'owner_id': u'bob'}}
        game = self.container.load_game("games_0")

    def testSavePlayer(self):
        self.player = PlayerActor(self.room2, "player",
            Script("rooms.script", "rooms.script"),
            "bob", game_id="games_0", actor_id="id1")

        self.assertFalse(self.container.player_exists("bob", "games_0"))
        self.container.save_player(self.player)
        self.assertTrue(self.container.player_exists("bob", "games_0"))

        expected = {'actors_0': {u'__type__': u'PlayerActor',
              '_id': 'actors_0',
              "_loadstate": None,
              u'actor_id': u'id1',
              u'status': None,
              u'parent_id': None,
              u'actor_type': u'player',
              u'game_id': u'games_0',
              u'path': [{u'__type__': u'Vector',
                         u'end_pos': {u'__type__': u'Position',
                                      u'x': 0.0,
                                      u'y': 0.0,
                                      u'z': 0.0},
                         u'end_time': 0.0,
                         u'start_pos': {u'__type__': u'Position',
                                        u'x': 0.0,
                                        u'y': 0.0,
                                        u'z': 0.0},
                         u'start_time': 0}],
              u'room_id': u'room2',
              u'script_name': u'rooms.script',
              u'speed': 1.0,
              u'state': {},
              u'state': {u'__type__': u'SyncState'},
              u'username': u'bob',
              u'docked_with': None,
              u'visible': True,
              u'token': None,
              u'timeout_time': None,
              u'initialized': False,
        }}
        self.assertEquals(expected, self.dbase.dbases['actors'])

    def testLoadPlayer(self):
        self.dbase.dbases['actors'] = {'id1': {u'__type__': u'PlayerActor',
            '_id': 'id1',
            u'actor_id': u'id1',
            u'actor_type': u'player',
            u'status': None,
            u'game_id': u'games_1',
            u'script_name': u'rooms.container_test',
            u'room_id': u'rooms_10',
            "visible": True,
            "parent_id": None,
            "docked_with": None,
            "state": {"__type__": "SyncState"},
            "path": [],
            "speed": 1.0,
            "path": [{"__type__": "Vector",
                      "end_pos": {"__type__": "Position",
                                  "x": 10.0,
                                  "y": 10.0,
                                  "z": 0.0},
                      "end_time": 0.0,
                      "start_pos": {"__type__": "Position",
                                    "x": 10.0,
                                    "y": 10.0,
                                    "z": 0.0},
                      "start_time": 0}],
            "token": None,
            "timeout_time": None,
            u'username': u'ned'}}

        player = self.container.load_player("ned", "games_1")

        self.assertEquals("rooms_10", player.room_id)
        self.assertEquals("id1", player._id)
        self.assertEquals(Position(10, 10), player.position)

        self.assertRaises(Exception,
            self.container.load_player, "ned", "nonexistant")

    def testCreatePlayer(self):
        player = self.container.create_player(self.room2, "player",
            Script("rooms.container_test", "rooms.container_test"),
            "ned", game_id="games_0")
        self.assertEquals("actors_0", player._id)
        self.assertEquals("ned", player.username)
        self.assertEquals("games_0", player.game_id)
        self.assertEquals("room2", player.room_id)

    def testLoadRoom(self):
        self.dbase.dbases['rooms'] = {}
        self.dbase.dbases['rooms']['rooms_0'] = { "_id": "rooms_0",
            "__type__": "Room", "room_id": "map1.room1", "game_id": "games_0",
            "script_name": "rooms.container_test",
            'state': {u'__type__': u'SyncState'},
            }
        self.dbase.dbases['actors'] = {}
        self.dbase.dbases['actors']['actor1'] = \
            {"__type__": "Actor", "_id": "actor1", "actor_id": None,
            "_loadstate": None,
            "parent_id": None,
            "game_id": "games_0", "room_id": "map1.room1",
            "actor_type": "test", "model_type": "model",
            "speed": 1.0,
            "username": "ned",
            "docked_with": None,
            "visible": True,
            'state': {u'__type__': u'SyncState'},
            "path": [], "vector": {"__type__": "Vector",
            "start_pos": {"__type__": "Position", "x": 0, "y": 0, "z": 0},
            "start_time": 0,
            "end_pos": {"__type__": "Position", "x": 0, "y": 10, "z": 0},
            "end_time": 10,
            }, "script_name": "rooms.container_test"}

        room = self.container.room_builder.create("games_0", "map1.room1")
        self.assertEquals(0, len(room.actors))
        self.assertEquals(1, len(room.doors))

    def testSaveRoom(self):
        room = Room("game1", "room1", self.node)
        room.coords(0, 0, 10, 10)
        actor = room.create_actor("mock_actor", "rooms.container_test")
        self.container.save_room(room)
        room_dict = self.dbase.dbases['rooms']['rooms_0']
        self.assertEquals('room1', room_dict['room_id'])
        actor_dict = self.dbase.dbases['actors']["actors_0"]
        expected = {u'__type__': u'Actor',
            '_id': 'actors_0',
            "_loadstate": None,
            u'actor_id': "id1",
            u'parent_id': None,
            u'actor_type': u'mock_actor',
            u'game_id': u'game1',
            u'path': [{u'__type__': u'Vector',
                        u'end_pos': {u'__type__': u'Position',
                                    u'x': 0.0,
                                    u'y': 0.0,
                                    u'z': 0.0},
                        u'end_time': 0.0,
                        u'start_pos': {u'__type__': u'Position',
                                    u'x': 0.0,
                                    u'y': 0.0,
                                    u'z': 0.0},
                        u'start_time': 0}],
            u'username': None,
            u'room_id': u'room1',
            u'script_name': u'rooms.container_test',
            u'speed': 1.0,
            u'docked_with': None,
            u'initialized': True,
            u'state': {u'__type__': u'SyncState'},
            u'visible': True}
        self.assertEquals(expected, actor_dict)

    def testOkWeveGotTheIdea(self):
        room = Room("games_0", "rooms_0", self.node)
        room.coords(0, 0, 50, 50)
        self.container.save_room(room)
        self.assertTrue(self.dbase.dbases['rooms'])

    def testSaveActor(self):
        room = Room("games_0", "rooms_0", self.node)
        room.coords(0, 0, 50, 50)
        actor = room.create_actor("mock_actor", "rooms.container_test",
            position=Position(20, 10))
        self.assertEquals(
            {u'__type__': u'Actor',
            '_id': 'actors_0',
            u'_loadstate': None,
            u'actor_id': u'id1',
            u'actor_type': u'mock_actor',
            u'docked_with': None,
            u'game_id': u'games_0',
            u'initialized': True,
            u'parent_id': None,
            u'path': [{u'__type__': u'Vector',
                        u'end_pos': {u'__type__': u'Position',
                                    u'x': 20.0,
                                    u'y': 10.0,
                                    u'z': 0.0},
                        u'end_time': 0.0,
                        u'start_pos': {u'__type__': u'Position',
                                    u'x': 20.0,
                                    u'y': 10.0,
                                    u'z': 0.0},
                        u'start_time': 0}],
            u'room_id': u'rooms_0',
            u'script_name': u'rooms.container_test',
            u'speed': 1.0,
            u'state': {u'__type__': u'SyncState'},
            u'username': None,
            u'visible': True},
            self.dbase.dbases['actors']['actors_0'])

        actor.state.testme = "value1"
        self.container.save_actor(actor)
        self.assertEquals({u'__type__': u'SyncState', u'testme': u'value1'},
            self.dbase.dbases['actors']['actors_0']['state'])

        actor.room = None
        actor._room_id = "newroom1"
        self.container.save_actor(actor)
        self.assertEquals("newroom1",
            self.dbase.dbases['actors']['actors_0']['room_id'])

        self.container.save_actor(actor, limbo=True)
        self.assertEquals("limbo",
            self.dbase.dbases['actors']['actors_0']['_loadstate'])

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

    def testUpdateRoom(self):
        room = MockRoom("game1", "room1")
        room._id = "room1"

        self.dbase.dbases['rooms'] = {}
        self.dbase.dbases['rooms']['room1'] = {'_id': "room1", "status": "inactive"}
        self.dbase.dbases['rooms']['room2'] = {'_id': "room2", "status": "inactive"}

        self.container.update_room(room, status="pending")

        self.assertEquals({'_id': "room1", "status": "pending"},
            self.dbase.dbases['rooms']['room1'])
        self.assertEquals({'_id': "room2", "status": "inactive"},
            self.dbase.dbases['rooms']['room2'])

    def testLoadPlayerVSLoadActor(self):
        room = MockRoom("game1", "room1")
        actor1 = Actor(room, "basic",
            Script("rooms.container_test", "rooms.container_test"),
            username="bob")
        player_actor1 = PlayerActor(room, "player",
            Script("rooms.container_test", "rooms.container_test"), "bob")

        self.container.save_actor(player_actor1)
        self.container.save_actor(actor1)

        loaded = self.container.load_player("bob", "game1")
        self.assertTrue(loaded.is_player)
        loaded_actor = self.container.load_actor("id1")
        self.assertFalse(loaded_actor.is_player)

    def testLoadPlayerOnly(self):
        room = MockRoom("game1", "room1")
        player_actor1 = PlayerActor(room, "player",
            Script("rooms.container_test", "rooms.container_test"), "bob")

        self.container.save_actor(player_actor1)

        loaded = self.container.load_player("bob", "game1")
        self.assertTrue(loaded.is_player)

    def testLoadPlayersForRoom(self):
        pass

    def testLoadObjectsFromLimbo(self):
        self.dbase.dbases['actors'] = {}
        self.dbase.dbases['actors']['actor1'] = \
            {"__type__": "Actor", "_id": "actor1", "actor_id": "actor1",
            "parent_id": None,
            "game_id": "games_0", "room_id": "room1",
            "actor_type": "test", "model_type": "model",
            "speed": 1.0,
            "username": "ned",
            "docked_with": None,
            "visible": True,
            'state': {u'__type__': u'SyncState'},
            "path": [], "vector": {"__type__": "Vector",
            "start_pos": {"__type__": "Position", "x": 0, "y": 0, "z": 0},
            "start_time": 0,
            "end_pos": {"__type__": "Position", "x": 0, "y": 10, "z": 0},
            "end_time": 10,
            }, "script_name": "rooms.container_test"}
        self.dbase.dbases['actors']['actor2'] = \
            {"__type__": "Actor", "_id": "actor2", "actor_id": "actor2",
            "parent_id": None,
            "game_id": "games_0", "room_id": "room1",
            "actor_type": "test", "model_type": "model",
            "_loadstate": "limbo",
            "speed": 1.0,
            "username": "ned",
            "docked_with": None,
            "visible": True,
            'state': {u'__type__': u'SyncState'},
            "path": [], "vector": {"__type__": "Vector",
            "start_pos": {"__type__": "Position", "x": 0, "y": 0, "z": 0},
            "start_time": 0,
            "end_pos": {"__type__": "Position", "x": 0, "y": 10, "z": 0},
            "end_time": 10,
            }, "script_name": "rooms.container_test"}

        actor = self.container.load_limbo_actor("games_0", "room1")
        self.assertEquals("actor2", actor.actor_id)

        self.assertEquals(None, self.container.load_limbo_actor("games_0", "room1"))

        # actor1 hasn't been affected (not in 'limbo')
        self.assertTrue('_loadstate' not in self.dbase.dbases['actors']['actor1'])
        # actor2 _loadstate blanked
        self.assertEquals(None, self.dbase.dbases['actors']['actor2']['_loadstate'])

    def testQueryUpdate(self):
        self.player = PlayerActor(self.room2, "player",
            Script("rooms.container_test", "rooms.container_test"),
            "bob", game_id="games_0")

        self.dbase.dbases['actors'] = {}
        self.container.find_and_modify_object('actors', self.player,
            query={'username': 'bob'}, upsert=True)

        actor_data = self.dbase.dbases['actors']['actors_0']
        self.assertEquals('id1', actor_data['actor_id'])
        self.assertEquals('bob', actor_data['username'])
        self.assertEquals('player', actor_data['actor_type'])
        self.assertEquals(None, actor_data['parent_id'])

        self.player.parent_id = 'id2'
        self.container.find_and_modify_object('actors', self.player,
            query={'username': 'bob'}, set_fields={'parent_id': 'id2'},
            upsert=True)

        self.assertEquals(1, len(self.container.dbase.dbases['actors']))
        actor_data = self.dbase.dbases['actors']['actors_0']
        self.assertEquals('id1', actor_data['actor_id'])
        self.assertEquals('bob', actor_data['username'])
        self.assertEquals('player', actor_data['actor_type'])
        self.assertEquals('id2', actor_data['parent_id'])

    def testRequestOrCreateRoom(self):
        self.assertEquals(0, len(self.dbase.dbases['rooms']))

        self.container.request_create_room("game1", "map1.room1")

        self.assertEquals(1, len(self.dbase.dbases['rooms']))
        self.assertEquals("game1", self.dbase.dbases['rooms']['rooms_0']['game_id'])

        # dont create if exists
        self.container.request_create_room("game1", "map1.room1")
        self.assertEquals(1, len(self.dbase.dbases['rooms']))
        self.assertEquals("game1", self.dbase.dbases['rooms']['rooms_0']['game_id'])

    def testLoadNextPendingRoom(self):
        room = self.container.load_next_pending_room('alpha')
        self.assertEquals(None, room)

        self.container.request_create_room("game1", "map1.room1")

        room = self.container.load_next_pending_room('alpha')
        room_data = self.container.dbase.dbases['rooms']['rooms_0']
        self.assertTrue(room_data['active'])
        self.assertFalse(room_data['requested'])
        self.assertEquals('alpha', room_data['node_name'])

    def testLoadNextPendingRoomDontLoadAssociatedRoom(self):
        self.container.request_create_room("game1", "map1.room1")
        self.container.dbase.dbases['rooms']['rooms_0']['node_name'] = 'beta'

        room = self.container.load_next_pending_room('alpha')
        self.assertEquals(None, room)

    def testUpdateMany(self):
        self.dbase.dbases['rooms']['rooms_0'] = {'__type__': 'Room',
                                           'node_name': 'alpha'}
        self.dbase.dbases['rooms']['rooms_1'] = {'__type__': 'Room',
                                           'node_name': 'dead_node'}
        self.dbase.dbases['rooms']['rooms_2'] = {'__type__': 'Room',
                                           'node_name': 'dead_node'}
        self.dbase.update_many_fields('rooms', {'node_name': 'dead_node'},
                                          {'node_name': None})

        self.assertEquals('alpha', self.dbase.dbases['rooms']['rooms_0']['node_name'])
        self.assertEquals(None, self.dbase.dbases['rooms']['rooms_1']['node_name'])
        self.assertEquals(None, self.dbase.dbases['rooms']['rooms_2']['node_name'])

    def testDisassociateRooms(self):
        self.dbase.dbases['rooms']['rooms_0'] = {'__type__': 'Room',
                                           'node_name': 'alpha'}
        self.dbase.dbases['rooms']['rooms_1'] = {'__type__': 'Room',
                                           'node_name': 'dead_node'}
        self.dbase.dbases['rooms']['rooms_2'] = {'__type__': 'Room',
                                           'node_name': 'dead_node'}
        self.container.disassociate_rooms('dead_node')

        self.assertEquals({'__type__': 'Room', 'node_name': 'alpha'},
                          self.dbase.dbases['rooms']['rooms_0'])
        self.assertEquals(
            {'active': False, 'requested': False, '__type__': 'Room',
             'node_name': None}, self.dbase.dbases['rooms']['rooms_1'])
        self.assertEquals(
            {'active': False, 'requested': False, '__type__': 'Room',
             'node_name': None}, self.dbase.dbases['rooms']['rooms_2'])

    def testLoadActorsForRoom(self):
        # loads some actors

        # assert _loadstate = ""
        pass

    def testListNodes(self):
        pass

    def testListGames(self):
        pass

    def testListPLayers(self):
        pass

    def testListActors(self):
        pass
