
import unittest

from player_actor import PlayerActor
from player import Player

class MockServer(object):
    def __init__(self):
        self.updates = []

    def send_update(self, game_id, username, update_id, **kwargs):
        self.updates.append((game_id, username, update_id, kwargs))

class PlayerActorTest(unittest.TestCase):
    def setUp(self):
        self.player1 = Player("player1", "games_0")
        self.player2 = Player("player2", "games_0")
        self.player_actor1 = PlayerActor(self.player1)
        self.player_actor2 = PlayerActor(self.player2)

        self.mock_server = MockServer()
        self.player_actor1.server = self.mock_server

    def testSendUpdate(self):
        self.player_actor1.send_update("hello", key=1)

        self.assertEquals([('games_0', 'player1', 'hello', {'key': 1})],
            self.mock_server.updates)
