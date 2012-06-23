
import random

from script import *


class MajorScript(Script):
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
            c("Excuse me Sir", "Yes, thank you, mines a brandy"),
            c("Where were you at the time of the murder?",
                "Yes, it's a little chilly, throw another log in the "
                "fireplace there's a good boy"),
        )
        return conv
