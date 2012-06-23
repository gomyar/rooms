
import random

from script import *
import random


class DilettanteScript(Script):
    def kickoff(self):
        self.set_state("random_wander")

    def state_random_wander(self):
        while True:
            room_x, room_y = self.npc.room.position
            x = random.randint(room_x, room_x + self.npc.room.width)
            y = random.randint(room_y, room_y + self.npc.room.height)
            self.walk_to(x, y)
            self.sleep(random.randint(2, 4))

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
