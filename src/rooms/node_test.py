
import unittest

from rooms.node import Node
from rooms.room import Room
from rooms.player import Player


class MockRoom(object):
    def __init__(self, game_id, room_id):
        self._kicked_off = False
        self.room_id = room_id
        self.game_id = game_id

    def kick(self):
        self._kicked_off = True


class MockContainer(object):
    def __init__(self, rooms=None, players=None):
        self.rooms = rooms or {}
        self.players = players or {}

    def load_room(self, game_id, room_id):
        return self.rooms[game_id, room_id]

    def save_room(self, room):
        self.rooms[room.game_id, room.room_id] = room

    def room_exists(self, game_id, room_id):
        return (game_id, room_id) in self.rooms

    def load_player(self, player_id):
        return self.players[player_id]


class MockScript(object):
    def __init__(self):
        self.called = []

    def call(self, method, *args, **kwargs):
        self.called.append((method, args, kwargs))


class MockPlayerScript(object):
    def __init__(self):
        self.room = None
        self.player = None

    def player_joins(self, player, room):
        self.player = player
        self.room = room


class MockGameScript(object):
    def __init__(self):
        self.room = None

    def room_created(self, room):
        self.room = room


class MockRpcClient(object):
    def __init__(self):
        self.registered_host = None
        self.registered_port = None
        self.registered = False
        self.online = True

    def register_node(self, host, port):
        self.registered_host, self.registered_port = host, port
        self.registered = True

    def deregister_node(self, host, port):
        self.registered_host, self.registered_port = host, port
        self.registered = False

    def offline_node(self, host, port):
        self.online = False


class NodeTest(unittest.TestCase):
    def setUp(self):
        self.player_script = MockScript()
        self.game_script = MockScript()
        self.mock_rpc = MockRpcClient()
        self.room1 = MockRoom("game1", "room1")
        self.player1 = Player("bob", "game1", "room1")
        self.container = MockContainer(rooms={("game1", "room1"): self.room1},
            players={"bob1": self.player1})
        self.node = Node("10.10.10.1", 8000, "master", 9000, self.container)
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

        self.assertEquals("10.10.10.1", self.mock_rpc.registered_host)
        self.assertEquals(8000, self.mock_rpc.registered_port)

    def testDeregister(self):
        self.mock_rpc.registered = True
        mockroom1 = MockRoom('game1', 'room1')
        mockroom2 = MockRoom('game1', 'room2')
        self.node.rooms['game1', 'room1'] = mockroom1
        self.node.rooms['game1', 'room2'] = mockroom2

        self.node.deregister()

        self.assertFalse(self.mock_rpc.registered)
        self.assertEquals("10.10.10.1", self.mock_rpc.registered_host)
        self.assertEquals(8000, self.mock_rpc.registered_port)
        self.assertFalse(self.mock_rpc.online)
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
        self.assertEquals([{'game_id': 'game1', 'room_id': 'room1'}],
            self.node.all_rooms())

    def testShutdown(self):
        pass
        # send offline signal

        # remove / serialize rooms

        # send deregister signal
