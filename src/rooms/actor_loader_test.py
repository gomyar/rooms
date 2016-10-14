
import unittest
from rooms.node import Node
from rooms.actor_loader import ActorLoader
from rooms.container import Container
from rooms.room import Room
from rooms.position import Position
from rooms.testutils import MockDbase
from testutils import MockTimer


class ActorLoaderTest(unittest.TestCase):
    def setUp(self):
        MockTimer.setup_mock()
        self.node = Node("localhost", 8000, "master", 7000)
        self.loader = ActorLoader(self.node)
        self.dbase = MockDbase()
        self.container = Container(self.dbase, self.node)
        self.node.container = self.container

        self.room1 = Room("game1", "room1", self.node)
        self.room1.coords(0, 0, 50, 50)
        self.node.rooms['games_0', 'map1.room1'] = self.room1
        self.room2 = Room("game1", "room2", self.node)
        self.room2.coords(0, 0, 50, 50)
        self.node.rooms['games_0', 'map1.room2'] = self.room2

        self.dbase.dbases['actors'] = {}
        self.dbase.dbases['actors']['actor1'] = \
            {"__type__": "Actor", "_id": "actor1", "actor_id": "actor1",
            "parent_id": None,
            "game_id": "games_0", "room_id": "map1.room1",
            "actor_type": "test", "model_type": "model",
            "speed": 1.0,
            "username": "ned",
            "docked_with": None,
            "visible": True,
            'state': {u'__type__': u'SyncDict'},
            "path": [], "vector": {"__type__": "Vector",
            "start_pos": {"__type__": "Position", "x": 0, "y": 0, "z": 0},
            "start_time": 0,
            "end_pos": {"__type__": "Position", "x": 0, "y": 10, "z": 0},
            "end_time": 10,
            }, "script_name": "mock_script"}

        self.dbase.dbases['actors']['actor2'] = \
            {"__type__": "Actor", "_id": "actor1", "actor_id": "actor2",
            "parent_id": None,
            "game_id": "games_0", "room_id": "map1.room1",
            "actor_type": "test", "model_type": "model",
            "_loadstate": "limbo",   # <---
            "speed": 1.0,
            "username": "ned",
            "docked_with": None,
            "visible": True,
            'state': {u'__type__': u'SyncDict'},
            "path": [], "vector": {"__type__": "Vector",
            "start_pos": {"__type__": "Position", "x": 0, "y": 0, "z": 0},
            "start_time": 0,
            "end_pos": {"__type__": "Position", "x": 0, "y": 10, "z": 0},
            "end_time": 10,
            }, "script_name": "mock_script"}

    def tearDown(self):
        MockTimer.teardown_mock()

    def testLoader(self):
        self.loader._load_actors()

        room = self.node.rooms['games_0', 'map1.room1']
        self.assertEquals(1, len(room.actors))

    def testLoaderDockedActors(self):
        self.dbase.dbases['actors']['actor3'] = \
            {"__type__": "Actor", "_id": "actor3", "actor_id": "actor3",
            "parent_id": None,
            "game_id": "games_0", "room_id": "map1.room1",
            "actor_type": "test", "model_type": "model",
            "_loadstate": "limbo",   # <---
            "speed": 1.0,
            "username": "ned",
            "docked_with": "actor2",
            "visible": True,
            'state': {u'__type__': u'SyncDict'},
            "path": [], "vector": {"__type__": "Vector",
            "start_pos": {"__type__": "Position", "x": 0, "y": 0, "z": 0},
            "start_time": 0,
            "end_pos": {"__type__": "Position", "x": 0, "y": 10, "z": 0},
            "end_time": 10,
            }, "script_name": "mock_script"}


        self.loader._load_actors()

        room = self.node.rooms['games_0', 'map1.room1']
        self.assertEquals(2, len(room.actors))

        actor2 = room.actors['actor2']
        actor3 = room.actors['actor3']

        self.assertEquals(actor2, actor3.docked_with)

    def testLoadDockedActorsWhichAlsoContainDockedActors(self):
        self.dbase.dbases['actors']['actor1'] = \
            {"__type__": "Actor", "_id": "actor1", "actor_id": "actor1",
            "parent_id": None,
            "game_id": "games_0", "room_id": "map1.room1",
            "actor_type": "test", "model_type": "model",
            "_loadstate": "limbo",   # <---
            "speed": 1.0,
            "username": "ned",
            "docked_with": None,
            "visible": True,
            'state': {u'__type__': u'SyncDict'},
            "path": [], "vector": {"__type__": "Vector",
            "start_pos": {"__type__": "Position", "x": 0, "y": 0, "z": 0},
            "start_time": 0,
            "end_pos": {"__type__": "Position", "x": 0, "y": 10, "z": 0},
            "end_time": 10,
            }, "script_name": "mock_script"}
        self.dbase.dbases['actors']['actor2'] = \
            {"__type__": "Actor", "_id": "actor2", "actor_id": "actor2",
            "parent_id": None,
            "game_id": "games_0", "room_id": "map1.room1",
            "actor_type": "test", "model_type": "model",
            "_loadstate": "limbo",   # <---
            "speed": 1.0,
            "username": "ned",
            "docked_with": "actor1",
            "visible": True,
            'state': {u'__type__': u'SyncDict'},
            "path": [], "vector": {"__type__": "Vector",
            "start_pos": {"__type__": "Position", "x": 0, "y": 0, "z": 0},
            "start_time": 0,
            "end_pos": {"__type__": "Position", "x": 0, "y": 10, "z": 0},
            "end_time": 10,
            }, "script_name": "mock_script"}
        self.dbase.dbases['actors']['actor3'] = \
            {"__type__": "Actor", "_id": "actor3", "actor_id": "actor3",
            "parent_id": None,
            "game_id": "games_0", "room_id": "map1.room1",
            "actor_type": "test", "model_type": "model",
            "_loadstate": "limbo",   # <---
            "speed": 1.0,
            "username": "ned",
            "docked_with": "actor2",
            "visible": True,
            'state': {u'__type__': u'SyncDict'},
            "path": [], "vector": {"__type__": "Vector",
            "start_pos": {"__type__": "Position", "x": 0, "y": 0, "z": 0},
            "start_time": 0,
            "end_pos": {"__type__": "Position", "x": 0, "y": 10, "z": 0},
            "end_time": 10,
            }, "script_name": "mock_script"}

        self.loader._load_actors()

        room = self.node.rooms['games_0', 'map1.room1']
        self.assertEquals(3, len(room.actors))

        actor1 = room.actors['actor1']
        actor2 = room.actors['actor2']
        actor3 = room.actors['actor3']

        self.assertEquals(actor1, actor2.docked_with)
        self.assertEquals(actor2, actor3.docked_with)


