import unittest
import gevent
import os

from rooms.testutils import MockRpcClient, MockContainer, MockTimer
from rooms.testutils import MockWebsocket, MockGeog, MockScript
from rooms.testutils import MockIDFactory
from rooms.node import Node
from rooms.room import Room
from rooms.player import PlayerActor
from rooms.position import Position
from rooms.actor import Actor
import rooms.actor
from rooms.script import Script
from rooms.room_factory import RoomFactory
from rooms.room_factory import FileMapSource

import logging
log = logging.getLogger("rooms.test")


class SystemTest(unittest.TestCase):
    def setUp(self):
        self.mock_rpc = MockRpcClient()
        self.mock_player_rpc = MockRpcClient()
        self.node = Node("10.10.10.1", 8000, "master", 9000)
        self.node._create_token = self._mock_create_token
        self._token_index = 0
        self.mock_script = MockScript()
        self.node.scripts["mock_script"] = self.mock_script
        self.node.scripts["player_script"] = Script("player_script", self)
        self.node.master_conn = self.mock_rpc
        self.node.master_player_conn = self.mock_player_rpc

        self.room1 = Room("game1", "map1.room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()

        self.container = MockContainer(
            room_factory=RoomFactory(
            FileMapSource(os.path.join(os.path.dirname(__file__),
            "test_maps")), self.node))
        self.container.node = self.node
        self.container.save_room(self.room1)

        self.container.save_actor(PlayerActor(self.room1,
            "player", self.mock_script, "bob",
            actor_id="player1"))

        self.node.container = self.container

        MockTimer.setup_mock()
        MockIDFactory.setup_mock()

    def _mock_create_token(self):
        self._token_index += 1
        return "TOKEN%s" % (self._token_index,)

    # script function
    def move_to(self, actor, x, y):
        log.debug("Moving %s to %s, %s", actor, x, y)
        actor.move_to(Position(x, y))

    # script function
    def ping(self, actor):
        print "PING"
        for i in range(10):
            actor.state.count = i
            actor.sleep(1)

    def tearDown(self):
        MockTimer.teardown_mock()
        MockIDFactory.teardown_mock()

    def testPlayerReceviesUpdatesFromRoom(self):
        self.node.manage_room("game1", "map1.room1")

        self.node.player_joins("fred", "game1", "map1.room1")
        self.node.player_joins("ned", "game1", "map1.room1")

        player1_ws = MockWebsocket()
        player2_ws = MockWebsocket()
        player1_gthread = gevent.spawn(self.node.player_connects, player1_ws,
            "game1", "TOKEN2")
        player2_gthread = gevent.spawn(self.node.player_connects, player2_ws,
            "game1", "TOKEN3")

        MockTimer.fast_forward(0)

        self.assertEquals(4, len(player1_ws.updates))
        self.assertEquals("sync", player1_ws.updates[0]['command'])
        self.assertEquals("actor_update", player1_ws.updates[1]['command'])
        self.assertEquals("actor_update", player1_ws.updates[2]['command'])

        self.assertEquals(4, len(player2_ws.updates))
        self.assertEquals("sync", player2_ws.updates[0]['command'])
        self.assertEquals("actor_update", player2_ws.updates[1]['command'])
        self.assertEquals("actor_update", player2_ws.updates[2]['command'])

        self.node.actor_call("game1", "TOKEN2", "id1", "move_to",
            x=10, y=10)

        MockTimer.fast_forward(0)

        self.assertEquals(5, len(player1_ws.updates))
        self.assertEquals("actor_update", player1_ws.updates[3]['command'])
        self.assertEquals(5, len(player2_ws.updates))
        self.assertEquals("actor_update", player2_ws.updates[3]['command'])

    def testPingUpdatesStateSendsActorUpdate(self):
        # Internal only ?
        self.node.manage_room("game1", "map1.room1")

        self.node.player_joins("ned", "game1", "map1.room1")

        player1_ws = MockWebsocket()
        player1_gthread = gevent.spawn(self.node.player_connects, player1_ws,
            "game1", "TOKEN2")

        self.node.actor_call("game1", "TOKEN2", "player1", "ping")

        MockTimer.fast_forward(1)

        self.assertEquals(0, player1_ws.updates[3]['data']['state']['count'])

        MockTimer.fast_forward(1)

        self.assertEquals(1, player1_ws.updates[4]['data']['state']['count'])

    def testInvalidToken(self):
        self.room1 = Room("game1", "map1.room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()
        self.container.save_room(self.room1)

        self.node.manage_room("game1", "map1.room1")

        self.node.player_joins("ned", "game1", "map1.room1")

        player1_ws = MockWebsocket()
        player1_gthread = gevent.spawn(self.node.player_connects, player1_ws,
            "game1", "TOKEN1")

        self.assertRaises(Exception, self.node.actor_call, "game1", "ned",
            "player1", "TOKEN2", "ping")

    def testExceptionIfNoSuchMethod(self):
        self.room1 = Room("game1", "map1.room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()
        self.container.save_room(self.room1)

        self.node.manage_room("game1", "map1.room1")

        self.node.player_joins("ned", "game1", "map1.room1")

        self.assertRaises(Exception, self.node.actor_call, "game1", "ned",
            "player1", "TOKEN2", "nonexistant")

    def testMultiPath(self):
        self.room1 = Room("game1", "map1.room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()
        self.container.save_room(self.room1)

        self.node.manage_room("game1", "map1.room1")

        self.node.player_joins("ned", "game1", "map1.room1")

        player1_ws = MockWebsocket()
        player1_gthread = gevent.spawn(self.node.player_connects, player1_ws,
            "game1", "TOKEN2")

        MockTimer.fast_forward(0)

        self.node.actor_call("game1", "TOKEN2", "player1", "move_to",
            x=10, y=10)

        MockTimer.fast_forward(0)

        self.assertEquals("actor_update", player1_ws.updates[3]['command'])
        self.assertEquals({u'x': 10.0, u'y': 10.0, u'z': 0.0},
            player1_ws.updates[3]['data']['vector']['end_pos'])

    def testMoveActorRoomSameNode(self):
        self.room1 = Room("game1", "map1.room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()
        self.container.save_room(self.room1)
        self.room2 = Room("game1", "map1.room2",
            Position(50, 0), Position(100, 50), self.node)
        self.room2.geography = MockGeog()
        self.container.save_room(self.room2)

        # add 2 rooms
        self.node.manage_room("game1", "map1.room1")
        self.node.manage_room("game1", "map1.room2")

        # add 1 player
        self.node.player_joins("ned", "game1", "map1.room1")

        # connect player
        ned_actor = self.node.rooms['game1', 'map1.room1'].actors['id1']

        # assert actor moves and player is updated
        self.node.move_actor_room(ned_actor, "game1", "map1.room2", Position(5, 5))
        # player is saved immediately, actor is put on save queue
        room2 = self.node.rooms["game1", "map1.room2"]
        self.assertEquals(ned_actor, room2.actors["id1"])
        self.assertEquals(room2, ned_actor.room)
        self.assertEquals({}, self.room1.actors)
        self.assertEquals(Position(5, 5), ned_actor.position)

    def testMoveActorRoomAnotherNode(self):
        self.room1 = Room("game1", "room1",
            Position(0, 0), Position(50, 50), self.node)
        self.room1.geography = MockGeog()
        self.container.save_room(self.room1)

        # add token to expects
        self.mock_rpc.expect['actor_entered'] = {
            "node": ["10.10.10.2", 8000], "token": "TOKEN2"}

        # add 1 room
        self.node.manage_room("game1", "map1.room1")

        # add 1 player
        self.node.player_joins("ned", "game1", "map1.room1")

        # connect player
        ned_actor = self.node.rooms['game1', 'map1.room1'].actors['id1']
        player_conn = self.node.player_connections['ned', 'game1']
        queue = player_conn.new_queue()

        # perform actor move
        self.node.move_actor_room(ned_actor, "game1", "map1.room2", Position(5, 5))

        # player is saved
        self.assertEquals("ned",
            self.container.dbase.dbases['actors']['actors_1']['username'])

        self.assertEquals({'actor_id': 'id1', 'command': 'remove_actor'},
            queue.get())
        self.assertEquals({'node': ['10.10.10.2', 8000], 'token': 'TOKEN2',
            'command': 'redirect'}, queue.get())
        self.assertEquals({}, self.room1.actors)
        self.assertEquals(Position(5, 5), ned_actor.position)

    def testMultiplePlayerConnections(self):
        # I'm gonna call this a known bug : when the same player connects
        # twice it re-sends the sync to the same players' other connections
        self.node.manage_room("game1", "map1.room1")

        self.node.player_joins("fred", "game1", "map1.room1")
        self.node.player_joins("ned", "game1", "map1.room1")

        player1_ws = MockWebsocket()
        player1_ws_2 = MockWebsocket()
        player2_ws = MockWebsocket()
        player1_gthread = gevent.spawn(self.node.player_connects, player1_ws,
            "game1", "TOKEN2")
        player1_g2 = gevent.spawn(self.node.player_connects, player1_ws_2,
            "game1", "TOKEN2")
        player2_gthread = gevent.spawn(self.node.player_connects, player2_ws,
            "game1", "TOKEN3")

        MockTimer.fast_forward(0)

        # extra sync messages here (8 instead of 4):
        self.assertEquals(8, len(player1_ws.updates))
        self.assertEquals(4, len(player1_ws_2.updates))
        self.assertEquals(4, len(player2_ws.updates))

        self.node.actor_call("game1", "TOKEN2", "id1", "move_to",
            x=10, y=10)

        MockTimer.fast_forward(0)

        self.assertEquals(9, len(player1_ws.updates))
        self.assertEquals(5, len(player1_ws_2.updates))
        self.assertEquals(5, len(player2_ws.updates))

    def testRemoveActorSignal(self):
        self.node.manage_room("game1", "map1.room1")

        self.node.player_joins("fred", "game1", "map1.room1")
        self.node.player_joins("ned", "game1", "map1.room1")

        player1_ws = MockWebsocket()
        player2_ws = MockWebsocket()
        player1_gthread = gevent.spawn(self.node.player_connects, player1_ws,
            "game1", "TOKEN1")
        player2_gthread = gevent.spawn(self.node.player_connects, player2_ws,
            "game1", "TOKEN1")

        MockTimer.fast_forward(0)

        room = self.node.rooms["game1", "map1.room1"]
        fred_actor = room.actors["id1"]
        self.node.actor_removed(room, fred_actor)

        MockTimer.fast_forward(0)

        self.assertEquals({"command": "remove_actor", "actor_id": "id1"},
            player2_ws.updates[-1])

    def testAdminConnection(self):
        self.node.manage_room("game1", "map1.room1")

        self.node.player_joins("fred", "game1", "map1.room1")
        adm_token = self.node.request_admin_token("game1", "map1.room1")

        player1_ws = MockWebsocket()
        player1_gthread = gevent.spawn(self.node.player_connects, player1_ws,
            "game1", "TOKEN2")
        admin_ws = MockWebsocket()
        admin_gthread = gevent.spawn(self.node.admin_connects, admin_ws,
            adm_token)

        MockTimer.fast_forward(0)

        self.assertEquals(3, len(player1_ws.updates))
        self.assertEquals(3, len(admin_ws.updates))

        self.node.actor_call("game1", "TOKEN2", "id1", "move_to",
            x=10, y=10)

        MockTimer.fast_forward(0)

        self.assertEquals(4, len(player1_ws.updates))
        self.assertEquals(4, len(admin_ws.updates))


