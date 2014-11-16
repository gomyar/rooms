
import unittest
import gevent

from rooms.atrunner import RoomsTestRunner
from rooms.atrunner import wait_for_sync
from rooms.atrunner import wait_for_position
from rooms.atrunner import wait_for_state
from rooms.atrunner import RoomsConnection

from gevent import monkey
monkey.patch_socket()

import logging
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class TwoNodesTest(unittest.TestCase):
    def setUp(self):
        self.game = RoomsTestRunner(__file__, './test_game_1')
        self.game.start_service(2)

        self.conn = RoomsConnection("localhost", 9000)

    def tearDown(self):
        self.game.stop_service()

    def testMoveBetweenNodes(self):
        game_id = self.conn.create_game("bob")

        info = self.conn.all_players_for("bob")
        self.conn.join_game("bob", game_id, "area1",
            "map1.room1", start_state="some value")

        wait_for_sync(self.conn, 2)

        self.conn.call_command("move_room", room_id="map1.room2")

        wait_for_position(self.conn.player_actor, (50, 0), 1000)
