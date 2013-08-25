
import unittest
from roomstestutils import *

class TwoNodesTest(unittest.TestCase):
    def setUp(self):
        self.game = RoomsTestRunner(__file__, './test_game_1')
        self.game.start_game(2)

        self.conn = open_connection()

    def tearDown(self):
        self.game.stop_game()

    def testTwoNodes(self):
        self.conn.create_game(owner_username="bob",
            game_id="735700000000000000000000")

        info = self.conn.player_info("bob", "735700000000000000000000")
        if not info:
            self.conn.join_game("bob", "735700000000000000000000", "area1",
                "room1", start_state="some value")
        else:
            self.conn.connect_to_game("bob", "735700000000000000000000")

        wait_for_sync(self.conn)

        self.conn.call("set_position", x=100, y=100)
        wait_for_position(self.conn.player_actor, (100, 100))

        self.conn.call("move_to", x=300, y=100)
        wait_for_position(self.conn.player_actor, (300, 100), 2.5)

