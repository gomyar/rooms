
import unittest

from npc_actor import NpcActor
from player_actor import PlayerActor
from script import Script
from script import chat
from script import c


class ScriptChatTest(unittest.TestCase):
    def setUp(self):
        self.npc = NpcActor("actor1")
        self.script = Script()
        self.script.npc = self.npc
        self.npc.npc_script = self.script
        self.npc.state = "beginstate"

        self.player = PlayerActor("player1")
        self.player.add_chat_message = self._mock_chat_message

    def _mock_chat_message(self, text, *args):
        self.player.log.append(dict(msg=text % args))

    def testChat(self):
        c("Goodbye", "Yes, goodbye")
        self.script.chat =  chat("Excuse me",
            "Yes?",
                c("Em, hello", "What do you want?",
                    c("Where is the jade monkey?", "No idea"),
                    c("Where are the toilets?",
                        "Second door on the left"),
                ),
                c("Goodbye", "Yes, goodbye"),
        )
        self.script.chat(self.player)

        self.assertEquals("chatting", self.player.state)
        self.assertEquals(self.npc, self.player.interacting_with)
        self.assertEquals(self.player, self.npc.interacting_with)
        self.assertEquals(2, len(self.player.log))
        self.assertEquals("Excuse me", self.player.log[0]['msg'])
        self.assertEquals("Yes?", self.player.log[1]['msg'])

        self.npc.chat("Em, hello")
        self.assertEquals("player1 says: Em, hello", self.player.log[2]['msg'])
        self.assertEquals("actor1 says: What do you want?",
            self.player.log[3]['msg'])
        self.npc.chat("Where is the jade monkey?")
        self.assertEquals("player1 says: Where is the jade monkey?",
            self.player.log[4]['msg'])
        self.assertEquals("actor1 says: No idea", self.player.log[5]['msg'])

        self.assertEquals("idle", self.player.state)
        self.assertEquals("beginstate", self.npc.state)
        self.assertEquals(None, self.player.interacting_with)
        self.assertEquals(None, self.npc.interacting_with)

        try:
            self.npc.chat("Goodbye")
            self.fail("Should have thrown")
        except AssertionError, ae:
            raise
        except Exception, e:
            self.assertEquals("Not understood", e.message)
