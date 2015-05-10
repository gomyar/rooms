
import unittest

from rooms.test_scripts import test_chat
from rooms.test_scripts import test_cheeseshop
from rooms.actor import Actor
from rooms.room import Room
from rooms.position import Position
from rooms.testutils import MockGridVision
from rooms.script import Script


class ChatStateTest(unittest.TestCase):
    def setUp(self):
        self.room = Room("game1", "map1.room1", Position(0, 0),
            Position(100, 100), None)
        self.vision = MockGridVision()
        self.room.vision = self.vision

        self.actor = Actor(None, "cheeseshop", Script("test_cheese",
            test_cheeseshop))
        self.player = Actor(None, "player", Script("test_chat", test_chat))

        self.room.put_actor(self.actor)
        self.room.put_actor(self.player)

    def testScriptChat(self):
        self.assertEquals("pong: hello",
            self.actor.script_call("ping", self.player, "hello"))

    def testCheeseShop(self):
        self.assertEquals(
            { "msg": "Hello Sir",
              "choices": [
                  (0, "I'd like to buy some cheese please"),
              ]
            },
            self.actor.script_call("start_conversation", self.player))
        self.assertEquals(
            { "msg": "What kind sir?",
              "choices": [
                (0, "Brie"),
                (1, "Cannonbear"),
                (2, "Stilton"),
              ]
            },
            self.actor.script_call("chat_response", self.player, 0))
        self.assertEquals(
            { "msg": "No Brie",
              "choices": [
                (1, "Cannonbear"),
                (2, "Stilton"),
              ]
            },
            self.actor.script_call("chat_response", self.player, 0))
        self.assertEquals(
            { "msg": "No Stilton",
              "choices": [
                (1, "Cannonbear"),
              ]
            },
            self.actor.script_call("chat_response", self.player, 2))

