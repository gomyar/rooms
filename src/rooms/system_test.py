import unittest
import gevent

from rooms.testutils import MockRpcClient, MockContainer, MockTimer
from rooms.testutils import MockWebsocket, MockGeog
from rooms.node import Node
from rooms.room import Room
from rooms.player import PlayerActor
from rooms.position import Position
from rooms.actor import Actor
import rooms.actor
from rooms.script import Script


class SystemTest(unittest.TestCase):
    def setUp(self):
        self.mock_rpc = MockRpcClient()
        self.mock_player_rpc = MockRpcClient()
        self.node = Node("10.10.10.1", 8000, "master", 9000)
        self.node._create_token = lambda: "TOKEN1"
        self.node.load_player_script("rooms.test_scripts.basic_player")
        self.node.master_conn = self.mock_rpc
        self.node.master_player_conn = self.mock_player_rpc

        self.room1 = Room("game1", "room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()

        self.container = MockContainer()
        self.container.rooms['game1', 'room1'] = self.room1

        self.container.player_actors['bob', 'game1'] = PlayerActor(self.room1,
            "player", "rooms.test_scripts.basic_player", "bob",
            actor_id="player1")

        self.node.container = self.container

        MockTimer.setup_mock()

    def tearDown(self):
        MockTimer.teardown_mock()

    def testPlayerReceviesUpdatesFromRoom(self):
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

        self.assertEquals(3, len(player1_ws.updates))
        self.assertEquals("sync", player1_ws.updates[0]['command'])
        self.assertEquals("actor_update", player1_ws.updates[1]['command'])
        self.assertEquals("actor_update", player1_ws.updates[2]['command'])

        self.assertEquals(3, len(player2_ws.updates))
        self.assertEquals("sync", player2_ws.updates[0]['command'])
        self.assertEquals("actor_update", player2_ws.updates[1]['command'])
        self.assertEquals("actor_update", player2_ws.updates[2]['command'])


        self.node.actor_call("game1", "bob", "player1", "move_to", x=10, y=10,
            token="TOKEN1")

        MockTimer.fast_forward(0)

        self.assertEquals(4, len(player1_ws.updates))
        self.assertEquals("actor_update", player1_ws.updates[3]['command'])
        self.assertEquals(4, len(player2_ws.updates))
        self.assertEquals("actor_update", player2_ws.updates[3]['command'])

    def testPing(self):
        self.container.player_actors['bob', 'game1'] = PlayerActor(self.room1,
            "player", "rooms.test_scripts.basic_player", "bob",
            actor_id="player1")

        self.room1 = Room("game1", "room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()
        self.container.rooms['game1', 'room1'] = self.room1

        self.node.manage_room("game1", "room1")

        self.node.player_joins("bob", "game1", "room1")

        player1_ws = MockWebsocket()
        player1_gthread = gevent.spawn(self.node.player_connects, player1_ws,
            "game1", "bob", "TOKEN1")

        self.node.actor_call("game1", "bob", "player1", "ping", token="TOKEN1")

        MockTimer.fast_forward(1)

        self.assertEquals({"command": "actor_update", "actor_id": "player1",
            "data": {'count': 0}}, player1_ws.updates[2])
        self.assertEquals({"command": "actor_update", "actor_id": "player1",
            "data": {'count': 1}}, player1_ws.updates[3])

    def testInvalidToken(self):
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
            "player1", "ping", token="TOKEN2")

    def testExceptionIfNoSuchMethod(self):
        self.room1 = Room("game1", "room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()
        self.container.rooms['game1', 'room1'] = self.room1

        self.node.manage_room("game1", "room1")

        self.node.player_joins("bob", "game1", "room1")

        self.assertRaises(Exception, self.node.actor_call, "game1", "bob",
            "player1", "nonexistant")

    def testMultiPath(self):
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

        self.node.actor_call("game1", "bob", "player1", "move_to", x=10, y=10,
            token="TOKEN1")

        MockTimer.fast_forward(0)

        self.assertEquals("actor_update", player1_ws.updates[2]['command'])
        self.assertEquals({u'x': 10.0, u'y': 10.0, u'z': 0.0},
            player1_ws.updates[2]['data']['vector']['end_pos'])

    def testMoveActorRoomSameNode(self):
        self.room1 = Room("game1", "room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()
        self.container.rooms['game1', 'room1'] = self.room1

        # add 2 rooms
        self.node.manage_room("game1", "room1")
        self.node.manage_room("game1", "room2")

        # add 1 player
        self.node.player_joins("bob", "game1", "room1")

        # connect player
        self.player = self.container.player_actors['bob', 'game1']

        # assert actor moves and player is updated
        self.node.move_actor_room(self.player, "game1", "room2", Position(5, 5))
        # player is saved immediately, actor is put on save queue
        room2 = self.node.rooms["game1", "room2"]
        self.assertEquals(self.player, room2.actors["player1"])
        self.assertEquals(room2, self.player.room)

    def testMoveActorRoomAnotherNode(self):
        self.room1 = Room("game1", "room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()
        self.container.rooms['game1', 'room1'] = self.room1

        self.mock_player_rpc.expect['player_connects'] = {"token": "TOKEN2",
            "node": ["10.10.10.2", 8000]}

        # add 1 room
        self.node.manage_room("game1", "room1")

        # add 1 player
        self.node.player_joins("bob", "game1", "room1")

        # connect player
        self.player = self.container.player_actors['bob', 'game1']
        queue = self.player.queue

        # perform actor move
        self.node.move_actor_room(self.player, "game1", "room2", Position(5, 5))
        # player is saved immediately
        self.assertEquals([(self.player, {"room_id": "room2"})],
            self.container.actor_updates)

        self.assertEquals({'node': ['10.10.10.2', 8000], 'token': 'TOKEN2',
            'command': 'redirect'}, queue.get())
        self.assertEquals([
            ('player_connects', {'game_id': 'game1', 'username': 'bob'})],
            self.mock_player_rpc.called)
