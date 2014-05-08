
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
        gevent.spawn(self.node.player_connects, player1_ws, "game1", "bob",
            "TOKEN1")
        gevent.spawn(self.node.player_connects, player2_ws, "game1", "ned",
            "TOKEN1")

        MockTimer.fast_forward(0)

        self.assertEquals([{u'actor_id': u'actor2',
            u'state': {},
            u'vector': {u'end_pos': [0, 0, 0],
                u'end_time': 0,
                u'start_pos': [0, 0, 0],
                u'start_time': 0}},
            {u'actor_id': u'actor1',
            u'state': {},
            u'vector': {u'end_pos': [0, 0, 0],
                u'end_time': 0,
                u'start_pos': [0, 0, 0],
                u'start_time': 0}}]
            , player1_ws.updates)
        self.assertEquals([{u'actor_id': u'actor2',
            u'state': {},
            u'vector': {u'end_pos': [0, 0, 0],
                u'end_time': 0,
                u'start_pos': [0, 0, 0],
                u'start_time': 0}},
            {u'actor_id': u'actor1',
            u'state': {},
            u'vector': {u'end_pos': [0, 0, 0],
                u'end_time': 0,
                u'start_pos': [0, 0, 0],
                u'start_time': 0}}]
            , player2_ws.updates)

        self.node.actor_call("game1", "bob", "actor1", "move_to", "[10, 10]")

        MockTimer.fast_forward(0)

        self.assertEquals({'vector': {u'end_pos': [0, 0, 0],
                u'end_time': 0,
                u'start_pos': [0, 0, 0],
                u'start_time': 0}}, player1_ws.updates[2])
        self.assertEquals({'vector': {u'end_pos': [0, 0, 0],
                u'end_time': 0,
                u'start_pos': [0, 0, 0],
                u'start_time': 0}}, player2_ws.updates[2])
