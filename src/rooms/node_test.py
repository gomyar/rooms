
import unittest

from rooms.node import Node
from rooms.room import Room
from rooms.player import Player
from rooms.testutils import MockContainer
from rooms.testutils import MockRpcClient
from rooms.testutils import MockScript
from rooms.testutils import MockRoom
from rooms.rpc import RPCException


class NodeTest(unittest.TestCase):
    def setUp(self):
        self.player_script = MockScript()
        self.game_script = MockScript()
        self.mock_rpc = MockRpcClient()
        self.room1 = MockRoom("game1", "room1")
        self.player1 = Player("bob", "game1", "room1")
        self.container = MockContainer(rooms={("game1", "room1"): self.room1},
            players={"bob1": self.player1})
        self.node = Node("10.10.10.1", 8000, "master", 9000)
        self.node.container = self.container
        self.node._create_token = lambda: "TOKEN1"
        self.node.player_script = self.player_script
        self.node.game_script = self.game_script
        self.node.master_conn = self.mock_rpc

    def testManageRoom(self):
        self.node.manage_room("game1", "room1")

        self.assertEquals(1, len(self.node.rooms))
        self.assertTrue(self.room1._kicked_off)

    def testPlayerJoins(self):
        self.node.manage_room("game1", "room1")
        self.container.players['bob', 'game1'] = Player('bob', 'game1', 'room1')
        token = self.node.player_joins("bob", "game1", "room1")
        self.assertEquals("TOKEN1", token)

        self.assertEquals(1, len(self.node.players))
        self.assertEquals([
            ("player_joins", (self.player1, self.room1), {})
        ], self.player_script.called)

    def testManageNonExistantRoom(self):
        self.node.manage_room("game1", "room2")
        self.assertEquals(2, len(self.container.rooms))
        self.assertEquals([("room_created",
            (self.container.rooms['game1', 'room2'],), {})],
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
        # expects player to exist in dbase
        self.container.players['bob', 'game1'] = Player('bob', 'game1', 'room1')
        token = self.node.player_joins("bob", "game1", "room1")
        self.assertEquals([{'username': 'bob', 'game_id': 'game1',
            'token': 'TOKEN1', 'room_id': 'room1'}], self.node.all_players())

    def testAllRooms(self):
        self.node.manage_room("game1", "room1")
        self.assertEquals([{'game_id': 'game1', 'room_id': 'room1'}],
            self.node.all_rooms())

    def testRequestToken(self):
        self.node.manage_room("game1", "room1")
        self.container.players['bob', 'game1'] = Player("bob", "game1", "room1")
        token = self.node.request_token("bob", "game1")
        self.assertEquals("TOKEN1", token)

    def testRequestTokenInvalidPlayer(self):
        self.node.manage_room("game1", "room_other")
        self.container.players['bob', 'game1'] = Player("bob", "game1", "room1")
        self.assertRaises(RPCException, self.node.request_token, "bob", "game1")

    def testRequestTokenNoSuchPlayer(self):
        self.node.manage_room("game1", "room_other")
        self.container.players['bob', 'game1'] = Player("bob", "game1", "room1")
        self.assertRaises(RPCException, self.node.request_token, "no", "game1")
