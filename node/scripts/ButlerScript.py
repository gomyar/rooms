
import random

from scriptutils import *


class ButlerScript(Script):
    def kickoff(self):
        self.npc.set_state("greeting_guests")

    def state_greeting_guests(self):
        while True:
            self.walk_to(930, 1740)
            self.walk_to(935, 1740)
            self.walk_to(1180, 1740)
            self.walk_to(1180, 1590)
            self.walk_to(930, 1590)

    def event_player_moved_nearby(self, player_actor):
        player_actor.add_chat_message("Good evening, Sir")
