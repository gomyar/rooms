
import unittest
from rooms.node import Node
from rooms.actor_loader import ActorLoader
from rooms.container import Container
from rooms.testutils import MockRoom
from rooms.testutils import MockDbase


class ActorLoaderTest(unittest.TestCase):
    def setUp(self):
        self.node = Node("localhost", 8000, "master", 7000)
        self.loader = ActorLoader(self.node)
        self.dbase = MockDbase()
        self.container = Container(self.dbase, None, self.node, None)
        self.node.container = self.container

        self.node.rooms['map1.room1'] = MockRoom("game1", "map1.room1")
        self.node.rooms['map1.room2'] = MockRoom("game1", "map1.room2")

        self.dbase.dbases['actors'] = {}
        self.dbase.dbases['actors']['actor1'] = \
            {"__type__": "Actor", "_id": "actor1", "actor_id": "actor1",
            "game_id": "games_0", "room_id": "map1.room1",
            "actor_type": "test", "model_type": "model",
            "speed": 1.0,
            "username": "ned",
            'state': {u'__type__': u'SyncDict'},
            "path": [], "vector": {"__type__": "Vector",
            "start_pos": {"__type__": "Position", "x": 0, "y": 0, "z": 0},
            "start_time": 0,
            "end_pos": {"__type__": "Position", "x": 0, "y": 10, "z": 0},
            "end_time": 10,
            }, "script_name": "mock_script"}

        self.dbase.dbases['actors']['actor2'] = \
            {"__type__": "Actor", "_id": "actor1", "actor_id": "actor2",
            "game_id": "games_0", "room_id": "map1.room1",
            "actor_type": "test", "model_type": "model",
            "_loadstate": "limbo",   # <---
            "speed": 1.0,
            "username": "ned",
            'state': {u'__type__': u'SyncDict'},
            "path": [], "vector": {"__type__": "Vector",
            "start_pos": {"__type__": "Position", "x": 0, "y": 0, "z": 0},
            "start_time": 0,
            "end_pos": {"__type__": "Position", "x": 0, "y": 10, "z": 0},
            "end_time": 10,
            }, "script_name": "mock_script"}

    def testLoader(self):
        self.loader._load_actors()

        self.assertEquals(1, len(self.node.rooms['map1.room1'].actors))
