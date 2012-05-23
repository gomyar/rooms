
import random

from scriptutils import *


class GladysScript(Script):
    def kickoff(self):
        self.set_state("arranging_dining_room")

    def state_arranging_dining_room(self):
        while True:
            self.walk_to(800, 220)
            self.sleep(10)
            self.walk_to(880, 520)
            self.sleep(5)
            self.walk_to(880, 440)
            self.sleep(5)
            self.walk_to(880, 360)
            self.sleep(5)
            self.walk_to(870, 150)
            self.sleep(5)
            self.walk_to(1160, 100)
            self.sleep(5)

    def chat(self, player):
        return chat(
            c("Excuse me madame", "Yes, Good evening.",
                c("When will dinner be ready?", "When cook says so.",
                    c("Whats holding up the cook?",
                        "Well, she's a perfectionist you see."),
                    c("Could I grab something from the kitchen?",
                        "Certainly not, it will ruin your apetite, you'll "
                        "insult Cook."),
                ),
            )
        )
