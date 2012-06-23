
import random

from script import *


class AuntScript(Script):
    def kickoff(self):
        self.set_state("pottering_around_lounge")

    def state_pottering_around_lounge(self):
        while True:
            self.walk_to(830, 620)
            self.sleep(2)
            self.walk_to(860, 460)
            self.sleep(3)
            self.walk_to(850, 690)
            self.sleep(2)
            self.walk_to(1170, 690)
            self.sleep(3)
            self.walk_to(1030, 720)
            self.sleep(5)

    def chat(self, player):
        conv = chat(
            c("Excuse me madame", "What? Yes, what? Speak up Deary...",
                c("How can I find the Dining Room?",
                    "Sorry Deary, you'll have to speak up..."),
                c("How are you feeling?",
                    "Sorry Deary, you'll have to speak up..."),
                c("Where were you at the time of the murder?",
                    "Sorry Deary, you'll have to speak up..."),
            )
        )
        return conv
