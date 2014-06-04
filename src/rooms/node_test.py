
import unittest
import gevent
from gevent.queue import Queue

from rooms.node import Node
from rooms.room import Room
from rooms.player import PlayerActor
from rooms.testutils import MockContainer
from rooms.testutils import MockRpcClient
from rooms.testutils import MockScript
from rooms.testutils import MockRoom
from rooms.testutils import MockTimer
from rooms.testutils import MockWebsocket
from rooms.testutils import MockActor
from rooms.testutils import MockRoomFactory
from rooms.rpc import RPCException
from rooms.position import Position


class NodeTest(unittest.TestCase):
    def setUp(self):
        self.player_script = MockScript()
        self.game_script = MockScript()
        self.mock_rpc = MockRpcClient()
        self.room1 = MockRoom("game1", "room1")
        self.room2 = MockRoom("game1", "room2")
        self.mock_room_factory = MockRoomFactory(self.room2)
        self.player1 = PlayerActor(self.room1, "player", "rooms.node_test",
            "bob")
        self.container = MockContainer(rooms={("game1", "room1"): self.room1},
            player_actors={("bob1", "game1"): self.player1},
            room_factory=self.mock_room_factory)
        self.node = Node("10.10.10.1", 8000, "master", 9000)
        self.node.container = self.container
        self.node._create_token = lambda: "TOKEN1"
        self.node.player_script = self.player_script
        self.node.game_script = self.game_script
        self.node.master_conn = self.mock_rpc
        MockTimer.setup_mock()

    def tearDown(self):
        MockTimer.teardown_mock()

    def testManageRoom(self):
        self.node.manage_room("game1", "room1")

        self.assertEquals(1, len(self.node.rooms))
        self.assertTrue(self.room1._kicked_off)

    def testPlayerJoins(self):
        self.node.manage_room("game1", "room1")

        token = self.node.player_joins("bob", "game1", "room1")
        self.assertEquals("TOKEN1", token)

        new_player = self.container.player_actors['bob', 'game1']
        self.assertEquals("bob", new_player.username)
        self.assertEquals("room1", new_player.room_id)
        self.assertEquals("game1", new_player.game_id)
        self.assertEquals(1, len(self.node.players))
        self.assertEquals([
            ("player_joins", (new_player, self.room1), {})
        ], self.player_script.called)

    def testManageNonExistantRoom(self):
        self.node.manage_room("game1", "room2")
        self.assertEquals(2, len(self.container.rooms))
        self.assertEquals([("room_created",
            (self.room2,), {})],
            self.game_script.called)

    def testConnectToMaster(self):
        self.node.connect_to_master()

        self.assertEquals([
            ('register_node', {'host': '10.10.10.1', 'port': 8000})],
            self.mock_rpc.called)

    def testDeregister(self):
        mockroom1 = MockRoom('game1', 'room1')
        mockroom2 = MockRoom('game1', 'room2')
        self.node.rooms['game1', 'room1'] = mockroom1
        self.node.rooms['game1', 'room2'] = mockroom2

        self.node.deregister()

        self.assertEquals([
            ('offline_node', {'host': '10.10.10.1', 'port': 8000}),
            ('deregister_node', {'host': '10.10.10.1', 'port': 8000})],
            self.mock_rpc.called)

        self.assertEquals({('game1', 'room1'): mockroom1,
            ('game1', 'room2'): mockroom2}, self.container.rooms)

    def testOfflineBouncesAllConnectedToMaster(self):
        pass

    def testSerializeQueue(self):
        pass

    def testOfflineWaitsForSerializeQueue(self):
        pass

    def testAllPlayers(self):
        self.node.manage_room("game1", "room1")
        token = self.node.player_joins("bob", "game1", "room1")
        self.assertEquals([{'username': 'bob', 'game_id': 'game1',
            'token': 'TOKEN1', 'room_id': 'room1'}], self.node.all_players())

    def testAllRooms(self):
        self.node.manage_room("game1", "room1")
        self.assertEquals([
            {'actors': [], 'game_id': 'game1', 'room_id': 'room1'}],
            self.node.all_rooms())

    def testRequestToken(self):
        self.node.manage_room("game1", "room1")
        self.container.player_actors['bob', 'game1'] = self.player1
        token = self.node.request_token("bob", "game1")
        self.assertEquals("TOKEN1", token)

    def testRequestTokenInvalidPlayer(self):
        self.node.manage_room("game1", "room_other")
        self.container.player_actors['bob', 'game1'] = self.player1
        self.assertRaises(RPCException, self.node.request_token, "bob", "game1")

    def testRequestTokenNoSuchPlayer(self):
        self.node.manage_room("game1", "room_other")
        self.container.player_actors['bob', 'game1'] = self.player1
        self.assertRaises(RPCException, self.node.request_token, "no", "game1")

    def testPlayerConnects(self):
        ws = MockWebsocket()
        gevent.spawn(self.node.ping, ws)

        MockTimer.fast_forward(0)
        self.assertEquals([0], ws.updates)

        MockTimer.fast_forward(1)
        self.assertEquals([0, 1], ws.updates)

        MockTimer.fast_forward(1)
        self.assertEquals([0, 1, 2], ws.updates)

        MockTimer.fast_forward(3)
        self.assertEquals([0, 1, 2, 3, 4, 5], ws.updates)

    def testActorCall(self):
        self.node.manage_room("game1", "room1")
        self.container.player_actors['bob', 'game1'] = self.player1
        self.node.player_joins("bob", "game1", "room1")
        actor = MockActor()
        self.room1.actors['actor1'] = actor

        self.node.actor_call("game1", "bob", "actor1", "do_something",
            token="TOKEN1")

        self.assertEquals([('do_something', (actor,), {})], actor.script.called)

    def testNonPlayerActorMovesNode(self):
        pass

    def testPlayerConnectsQueueDisconnectsOnRedirect(self):
        # node.player_connects will fall out of the connection naturally when
        # a redirect is given
        pass

