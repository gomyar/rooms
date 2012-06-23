
import random

from script import *


class ProfessorScript(Script):
    def kickoff(self):
        self.set_state("pottering_around_library")

    def state_pottering_around_library(self):
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
            c("Hello...", "Marty, quick we have to get you.., oh, never mind.",
                c("What did you just say?",
                    "Nothing, what can I do for you?"),
                c("Yes I'm looking for Doctor Willow",
                    "I don't know where he is, I have very important work to "
                    "do here, the experiment is in a critical state..."),
                c("What's that in the beaker?",
                    "Please don't touch that, very volatile, it's at a "
                    "critical stage."),
            )
        )
        return conv
