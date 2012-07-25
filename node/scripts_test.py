
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


