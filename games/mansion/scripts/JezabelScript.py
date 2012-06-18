
import random

from script import *


class JezabelScript(Script):
    def kickoff(self):
        self.set_state("pottering_around_dining_room")

    def state_pottering_around_dining_room(self):
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

    def storm_off(self):
        self.say("That's rude. Leave me alone")
        self.set_state("pottering_around_dining_room")

    def chat(self, player):
        return chat(
            c("Excuse me madame", "What? Yes, what do you want?",
                c("When will dinner be ready?",
                    "How should I know?"),
                c("Where were you at the time of the murder?",
                    self.storm_off),
                c("Well, is there a snack ready?",
                    "How would I know? Ask the cook."),
            )
        )
