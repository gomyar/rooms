
import random

from scriptutils import *


class ButlerScript(Script):
    def kickoff(self):
        self.npc.set_state("greeting_guests")

    def state_greeting_guests(self):
        while True:
            self.walk_to(930, 1740)
            self.walk_to(1180, 1740)
            self.walk_to(1180, 1590)
            self.walk_to(930, 1590)

    def chat(self, player):
        return chat("", "", [
            chat("", "Good evening, Sir", [
                chat("Have all the guests arrived yet?", "Not quite, Sir", [
                    chat("When is dinner starting?", "Around 9, Sir"),
                    chat("Where is the owner?",
                        "Lady Pinkerton in in the dining room, Sir"),
                ]),
                chat("Yes, thank you Jeeves, any chance of a drink?",
                    "The Lounge is straight ahead on the left, Sir")
            ])
        ])
