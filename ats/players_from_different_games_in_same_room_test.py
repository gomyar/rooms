
import unittest
from rooms.testutils import *


class PlayersFromDifferentGamesInSameRoom(unittest.TestCase):
    def setUp(self):
        self.game = RoomsTestRunner(__file__, './test_game_1')
        #self.game.start_game()

        self.conn_bob = open_connection()
        self.conn_ray = open_connection()

    def tearDown(self):
        self.game.stop_game()

    def testTwoNodes(self):
        bob_game_id = self.conn_bob.create_game(owner_username="bob")
        ray_game_id = self.conn_ray.create_game(owner_username="ray")

        info = self.conn_bob.player_info("bob", bob_game_id)
        if not info:
            self.conn_bob.join_game("bob", bob_game_id, "area1",
                "room1", start_state="some value")
        else:
            self.conn_bob.connect_to_game("bob", bob_game_id)

        info = self.conn_ray.player_info("ray", ray_game_id)
        if not info:
            self.conn_ray.join_game("ray", ray_game_id, "area1",
                "room1", start_state="some value")
        else:
            self.conn_ray.connect_to_game("ray", ray_game_id)

        wait_for_sync(self.conn_bob)
        wait_for_sync(self.conn_ray)

        wait_for_position(self.conn_ray.player_actor, (250, 250))
        wait_for_position(self.conn_bob.player_actor, (250, 250))

        self.assertEquals(1, len(self.conn_ray.actors))
        self.assertEquals("misteractor", self.conn_ray.actors.values()[0].name)
        self.assertEquals(1, len(self.conn_bob.actors))
        self.assertEquals("misteractor", self.conn_bob.actors.values()[0].name)


if __name__ == "__main__":
    unittest.main()
