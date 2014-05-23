
import unittest
import gevent

from rooms.testutils import MockRpcClient
from rooms.testutils import MockContainer
from rooms.node import Node
from rooms.room import Room
from rooms.player import Player
from rooms.position import Position
from rooms.testutils import MockTimer
from rooms.testutils import MockWebsocket
from rooms.testutils import MockGeog
from rooms.actor import Actor
import rooms.actor


class SystemTest(unittest.TestCase):
    def setUp(self):
        self.mock_rpc = MockRpcClient()
        self.player1 = Player("bob", "game1", "room1")
        self.container = MockContainer(players={"bob1": self.player1})
        self.node = Node("10.10.10.1", 8000, "master", 9000)
        self.node.container = self.container
        self.node._create_token = lambda: "TOKEN1"
        self.node.player_script.load_script("rooms.test_scripts.basic_player")
        self.node.master_conn = self.mock_rpc
        rooms.actor._create_actor_id = self._create_actor_id
        self._actor_id = 0
        MockTimer.setup_mock()

    def tearDown(self):
        MockTimer.teardown_mock()

    def _create_actor_id(self):
        self._actor_id = self._actor_id + 1
        return "actor%s" % (self._actor_id,)

    def testPlayerReceviesUpdatesFromRoom(self):
        self.container.players['bob', 'game1'] = Player("bob", "game1", "room1")
        self.container.players['ned', 'game1'] = Player("ned", "game1", "room1")
        self.room1 = Room("game1", "room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()
        self.container.rooms['game1', 'room1'] = self.room1

        self.node.manage_room("game1", "room1")

        self.node.player_joins("bob", "game1", "room1")
        self.node.player_joins("ned", "game1", "room1")

        player1_ws = MockWebsocket()
        player2_ws = MockWebsocket()
        player1_gthread = gevent.spawn(self.node.player_connects, player1_ws,
            "game1", "bob", "TOKEN1")
        player2_gthread = gevent.spawn(self.node.player_connects, player2_ws,
            "game1", "ned", "TOKEN1")

        MockTimer.fast_forward(0)

        self.assertEquals([
            {u'command': u'sync', u'data': {u'now': 0}},
            {u'command': u'actor_update', u'actor_id': u'actor2',
            u'data': {u'actor_id': u'actor2',
                        u'actor_type': u'',
                        u'model_type': u'',
                        u'state': {},
                        u'username': None,
                        u'vector': {u'end_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                                    u'end_time': 0.0,
                                    u'start_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                                    u'start_time': 0}}},
            {u'command': u'actor_update', u'actor_id': u'actor1',
            u'data': {u'actor_id': u'actor1',
                        u'actor_type': u'',
                        u'model_type': u'',
                        u'state': {},
                        u'username': None,
                        u'vector': {u'end_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                                    u'end_time': 0.0,
                                    u'start_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                                    u'start_time': 0}}}],
            player1_ws.updates)
        self.assertEquals([
            {u'command': u'sync', u'data': {u'now': 0}},
            {u'command': u'actor_update', u'actor_id': u'actor2',
            u'data': {u'actor_id': u'actor2',
                        u'actor_type': u'',
                        u'model_type': u'',
                        u'state': {},
                        u'username': None,
                        u'vector': {u'end_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                                    u'end_time': 0.0,
                                    u'start_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                                    u'start_time': 0}}},
            {u'command': u'actor_update', u'actor_id': u'actor1',
            u'data': {u'actor_id': u'actor1',
                        u'actor_type': u'',
                        u'model_type': u'',
                        u'state': {},
                        u'username': None,
                        u'vector': {u'end_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                                    u'end_time': 0.0,
                                    u'start_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                                    u'start_time': 0}}}],
            player2_ws.updates)

        self.node.actor_call("game1", "bob", "actor1", "move_to", x=10, y=10,
            token="TOKEN1")

        MockTimer.fast_forward(0)

        self.assertEquals({"command": "actor_update", "actor_id": "actor1",
            "data": {'vector': {u'end_pos': {u'x': 10.0, u'y': 10.0, u'z': 0.0},
                u'end_time': 14.142135623730951,
                u'start_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                u'start_time': 0}}}, player1_ws.updates[3])
        self.assertEquals({"command": "actor_update", "actor_id": "actor1",
            "data": {'vector': {u'end_pos': {u'x': 10.0, u'y': 10.0, u'z': 0.0},
                u'end_time': 14.142135623730951,
                u'start_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                u'start_time': 0}}}, player2_ws.updates[3])

    def testPing(self):
        self.container.players['bob', 'game1'] = Player("bob", "game1", "room1")
        self.room1 = Room("game1", "room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()
        self.container.rooms['game1', 'room1'] = self.room1

        self.node.manage_room("game1", "room1")

        self.node.player_joins("bob", "game1", "room1")

        player1_ws = MockWebsocket()
        player1_gthread = gevent.spawn(self.node.player_connects, player1_ws,
            "game1", "bob", "TOKEN1")

        self.node.actor_call("game1", "bob", "actor1", "ping", token="TOKEN1")

        MockTimer.fast_forward(1)

        self.assertEquals({"command": "actor_update", "actor_id": "actor1",
            "data": {'count': 0}}, player1_ws.updates[2])
        self.assertEquals({"command": "actor_update", "actor_id": "actor1",
            "data": {'count': 1}}, player1_ws.updates[3])

    def testInvalidToken(self):
        self.container.players['bob', 'game1'] = Player("bob", "game1", "room1")
        self.room1 = Room("game1", "room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()
        self.container.rooms['game1', 'room1'] = self.room1

        self.node.manage_room("game1", "room1")

        self.node.player_joins("bob", "game1", "room1")

        player1_ws = MockWebsocket()
        player1_gthread = gevent.spawn(self.node.player_connects, player1_ws,
            "game1", "bob", "TOKEN1")

        self.assertRaises(Exception, self.node.actor_call, "game1", "bob",
            "actor1", "ping", token="TOKEN2")

    def testExceptionIfNoSuchMethod(self):
        self.container.players['bob', 'game1'] = Player("bob", "game1", "room1")
        self.room1 = Room("game1", "room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()
        self.container.rooms['game1', 'room1'] = self.room1

        self.node.manage_room("game1", "room1")

        self.node.player_joins("bob", "game1", "room1")

        self.assertRaises(Exception, self.node.actor_call, "game1", "bob",
            "actor1", "nonexistant")

    def testMultiPath(self):
        self.container.players['bob', 'game1'] = Player("bob", "game1", "room1")
        self.room1 = Room("game1", "room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()
        self.container.rooms['game1', 'room1'] = self.room1

        self.node.manage_room("game1", "room1")

        self.node.player_joins("bob", "game1", "room1")

        player1_ws = MockWebsocket()
        player1_gthread = gevent.spawn(self.node.player_connects, player1_ws,
            "game1", "bob", "TOKEN1")

        MockTimer.fast_forward(0)

        self.node.actor_call("game1", "bob", "actor1", "move_to", x=10, y=10,
            token="TOKEN1")

        MockTimer.fast_forward(0)

        self.assertEquals({"command": "actor_update", "actor_id": "actor1",
            "data": {'vector': {u'end_pos': {u'x': 10.0, u'y': 10.0, u'z': 0.0},
                u'end_time': 14.142135623730951,
                u'start_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                u'start_time': 0}}}, player1_ws.updates[2])

