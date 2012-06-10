
import random

from script import *


class ButlerScript(Script):
    def kickoff(self):
        self.set_state("greeting_guests")

    def state_greeting_guests(self):
        while True:
            self.walk_to(930, 1740)
            self.sleep(5)
            self.walk_to(1180, 1740)
            self.sleep(5)
            self.walk_to(1180, 1590)
            self.sleep(5)
            self.walk_to(930, 1590)
            self.sleep(5)

    def chat(self, player):
        return chat(
            c("Hullo Jeeves", "Good evening, Sir",
                c("Have all the guests arrived yet?", "Not quite, Sir",
                    c("When is dinner starting?", "Around 9, Sir"),
                    c("Where is the owner?",
                        "Lady Pinkerton in in the dining room, Sir"),
                ),
                c("Yes, thank you Jeeves, any chance of a drink?",
                    "The Lounge is straight ahead on the left, Sir")
            )
        )
